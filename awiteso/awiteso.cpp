//
// An image to MIDI converter.
//
// `g++ -o awiteso -Wall -g awiteso.cpp -lboost_program_options -lpng`
//
// Copyright (C) 2009 by Andreas Stuehrk
//


#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include <boost/cstdint.hpp>
#include <boost/gil/extension/io/png_dynamic_io.hpp>
#include <boost/program_options.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/spirit/include/phoenix_container.hpp>
#include <boost/spirit/include/phoenix_core.hpp>
#include <boost/spirit/include/phoenix_object.hpp>
#include <boost/spirit/include/phoenix_operator.hpp>
#include <boost/spirit/include/phoenix_statement.hpp>
#include <boost/spirit/include/qi.hpp>

namespace bg = boost::gil;
namespace bpo = boost::program_options;
namespace bs = boost::spirit;


inline uint16_t byteswap(uint16_t n)
{
    return (n >> 8) | (n << 8);
}

inline uint32_t byteswap(uint32_t n)
{
    return (n >> 24) | ((n & 0x00ff0000) >> 8) | ((n & 0x0000ff00) << 8) |
           (n << 24);
}


// Base class for MIDI events
struct Event
{
    virtual ~Event() {}
    virtual void write_midi(std::ofstream&) const = 0;
};

// A generic NoteOnOff event
template <int EventCode>
struct NoteOnOff
: Event
{
    NoteOnOff(char pitch, char velocity=64)
    : pitch_(pitch), velocity_(velocity)
    {
    }

    virtual void
    write_midi(std::ofstream& outfile) const
    {
        char code = EventCode;
        outfile.write(&code, 1);
        outfile.write(&pitch_, 1);
        outfile.write(&velocity_, 1);
    }

    char pitch_;
    char velocity_;
};

typedef NoteOnOff<0x90> NoteOn;
typedef NoteOnOff<0x80> NoteOff;


struct Track
{
    void add_event(char, Event *);
    void write_midi(std::ofstream&) const;

    typedef std::vector<std::pair<char, boost::shared_ptr<Event> > > events_t;
    events_t events_;
};

void
Track::add_event(char delta, Event *event)
{
    events_.push_back(std::make_pair(delta, event));
}

void
Track::write_midi(std::ofstream& outfile) const
{
    // First, write track header
    outfile.write("MTrk", 4);
    // We only support note on and note off events right now, with a fixed
    // size of 4.
    // XXX Check endianess
    uint32_t length = byteswap(static_cast<uint32_t>(events_.size() * 4 + 4));
    outfile.write(reinterpret_cast<const char *>(&length), 4);

    // Now, write the events
    for (events_t::const_iterator it=events_.begin();
         it != events_.end(); ++it)
    {
        // Delta
        outfile.write(&it->first, 1);
        it->second->write_midi(outfile);
    }

    // Write meta event "end of track"
    outfile.write("\x00\xff\x2f\x00", 4);
}


struct Song
{
    Track& new_track();

    void write_midi(std::ofstream&) const;
    void write_midi(const std::string&) const;

    typedef std::vector<Track> tracks_t;
    tracks_t tracks_;
};

Track&
Song::new_track()
{
    tracks_.push_back(Track());
    return tracks_.back();
}

void
Song::write_midi(std::ofstream& outfile) const
{
    // Magic + header size (uint32, size=6 bytes) + format
    outfile.write("MThd\x00\x00\x00\x06\x00\x01", 10);
    // Number of tracks
    uint16_t ntracks = byteswap(static_cast<uint16_t>(tracks_.size()));
    outfile.write(reinterpret_cast<const char *>(&ntracks), 2);
    // division
    outfile.write("\x00\x5", 2);

    // Write tracks
    for (tracks_t::const_iterator it=tracks_.begin(); it != tracks_.end();
         ++it)
        it->write_midi(outfile);
}

void
Song::write_midi(const std::string& filename) const
{
    std::ofstream outfile(filename.c_str(), std::ios::out | std::ios::binary);
    write_midi(outfile);
    outfile.close();
}

enum byte_code
{
    op_add,
    op_sub,
    op_mul,
    op_div,
    op_pow,
    op_neg,
    op_const,
    op_load_x,
    op_load_y,
    op_load_z
};


struct ExpressionMachine
{
    ExpressionMachine()
    {
        stack_.reserve(4096);
    }

    typedef std::vector<int> code_t;
    int execute(const code_t& code, int x, int y, int z);

    std::vector<int> stack_;
};
typedef ExpressionMachine::code_t code_t;

int
ExpressionMachine::execute(const code_t& code, int x, int y, int z)
{
    code_t::const_iterator pc = code.begin();

    while (pc != code.end())
    {
        switch (*pc++)
        {
            case op_add:
            {
                int n = stack_.back();
                stack_.pop_back();
                stack_.back() += n;
                break;
            }
            case op_sub:
            {
                int n = stack_.back();
                stack_.pop_back();
                stack_.back() -= n;
                break;
            }
            case op_div:
            {
                int n = stack_.back();
                stack_.pop_back();
                stack_.back() /= n;
                break;
            }
            case op_mul:
            {
                int n = stack_.back();
                stack_.pop_back();
                stack_.back() *= n;
                break;
            }
            case op_pow:
            {
                int b = stack_.back();
                stack_.pop_back();
                int& a = stack_.back();
                a = pow(a, b);
                break;
            }
            case op_neg:
            {
                int& n = stack_.back();
                n = -n;
                break;
            }
            case op_const:
                stack_.push_back(*pc++);
                break;
            case op_load_x:
                stack_.push_back(x);
                break;
            case op_load_y:
                stack_.push_back(y);
                break;
            case op_load_z:
                stack_.push_back(z);
                break;
            default:
                throw std::runtime_error("Invalid opcode");
        }
    }

    return stack_.back();
}


template <typename Iterator>
struct Expression
: bs::qi::grammar<Iterator, bs::ascii::space_type>
{
    Expression(ExpressionMachine::code_t& code)
    : Expression::base_type(expr), code(code)
    {
        using bs::lexeme;
        using bs::lit;
        using bs::raw;
        using bs::arg_names::_1;
        using bs::ascii::alnum;
        using bs::ascii::alpha;
        using boost::phoenix::construct;
        using boost::phoenix::ref;
        using boost::phoenix::push_back;

        expr =
            term
            >> *( ('+' > term           [push_back(ref(code), op_add)])
                | ('-' > term           [push_back(ref(code), op_sub)])
                )
            ;

        term =
            power
            >> *( ('*' > power          [push_back(ref(code), op_mul)])
                | ('/' > power          [push_back(ref(code), op_div)])
                )
            ;

        power =
            factor
            >> *(('^' > factor)         [push_back(ref(code), op_pow)])
            ;

        factor =
            bs::uint_                   [push_back(ref(code), op_const),
                                         push_back(ref(code), _1)]
            | lit('x')                  [push_back(ref(code), op_load_x)]
            | lit('y')                  [push_back(ref(code), op_load_y)]
            | lit('z')                  [push_back(ref(code), op_load_z)]
            | ('(' >> expr >> ')')
            | ('+' > factor)
            | ('-' > factor             [push_back(ref(code), op_neg)])
            ;
    }

    typedef bs::qi::rule<Iterator, bs::ascii::space_type> rule_t;
    rule_t expr, factor, power, term;

    ExpressionMachine::code_t& code;
};


template <typename ViewT, typename PixelT>
void
get_diagonal(const ViewT& src, unsigned int x, unsigned int y,
                    std::vector<PixelT>& pixels)
{
    // Avoid reallocations
    pixels.reserve(pixels.size() +
                   floor(sqrt(pow(src.height() - y, 2) +
                         pow(src.width() - x, 2))));

    typename ViewT::xy_locator src_loc = src.xy_at(x, y);
    for (; x < src.width() && y < src.height();
         ++src_loc.x(), ++src_loc.y(), ++x, ++y)
        pixels.push_back(*src_loc);
}

template <typename ViewT, typename PixelT>
void
get_gray_diagonal(const ViewT& view, int x, int y, std::vector<PixelT>& pixels)
{
    get_diagonal(bg::color_converted_view<bg::gray8_pixel_t>(view), x, y,
                 pixels);
}


template <typename KeyT, typename T>
struct RangeMap
{
    template <typename KeyIterator, typename TIterator>
    RangeMap(KeyIterator kfirst, KeyIterator klast,
             TIterator first, TIterator last)
    : breakpoints_(kfirst, klast), values_(first, last)
    {}

    T
    operator[](const KeyT& key) const
    {
        typedef typename std::vector<KeyT>::const_iterator iter_t;
        iter_t it = lower_bound(breakpoints_.begin(), breakpoints_.end(), key);
        return values_[it - breakpoints_.begin()];
    }

    std::vector<KeyT> breakpoints_;
    std::vector<T> values_;
};


template <typename ViewT, typename NoteMap>
void
range_convert_image(const ViewT& view, Song& song, int ntracks,
              const NoteMap& note_map)
{
    for (; ntracks; --ntracks)
    {
        std::vector<short> note_pixels;
        get_gray_diagonal(view, ntracks * 4, 0, note_pixels);

        Track& track = song.new_track();

        typedef std::vector<short>::const_iterator iter_t;
        for (iter_t it=note_pixels.begin(); it != note_pixels.end();)
        {
            char note = note_map[*it];
            track.add_event(0, new NoteOn(note));

            iter_t begin = it++;
            while (it != note_pixels.end() && note_map[*it] == note)
                ++it;

            track.add_event((it - begin) * 1, new NoteOff(note));
        }
    }
}


template <typename ViewT, typename NoteMap>
void
polynomial_convert_image(const ViewT& view, Song& song,
                         const std::vector<code_t>& expressions,
                         const NoteMap& note_map)
{
    ExpressionMachine vm;

    for (std::vector<code_t>::const_iterator expr=expressions.begin();
         expr != expressions.end(); ++expr)
    {
        std::vector<typename ViewT::value_type> note_pixels;
        get_diagonal(view, 0, 0, note_pixels);

        Track& track = song.new_track();

        //typedef std::vector<short>::const_iterator iter_t;
        typedef typename std::vector<typename ViewT::value_type>
                         ::const_iterator iter_t;
        for (iter_t it=note_pixels.begin(); it != note_pixels.end();)
        {
            int x = (*it)[0];
            int y = (*it)[1];
            int z = (*it)[2];

            char note = note_map[vm.execute(*expr, x, y, z)];
            track.add_event(0, new NoteOn(note));

            iter_t begin = it++;
            while (it != note_pixels.end() &&
                   note_map[vm.execute(*expr, (*it)[0], (*it)[1], (*it)[2])]
                   == note)
                ++it;

            track.add_event((it - begin) * 1, new NoteOff(note));
        }
    }
}

int main(int argc, char **argv)
{
    int ntracks;
    std::vector<ExpressionMachine::code_t> expressions;
    std::vector<std::string> polynomials;

    // Create option descriptions
    bpo::options_description desc("Options");
    desc.add_options()
        ("help,h", "show help message and exit")
        ("input-file", bpo::value<std::string>(), "input image file")
        ("output-file", bpo::value<std::string>(), "output midi file")
        ("tracks,n", bpo::value<int>(&ntracks)->default_value(1),
         "number of tracks")
        ("range,R", "use a fixed range instead of polynomials")
        ("polynomials", bpo::value<std::vector<std::string> >());

    bpo::positional_options_description pos_desc;
    pos_desc.add("input-file", 1);
    pos_desc.add("output-file", 1);
    pos_desc.add("polynomials", -1);

    // Parse options
    bpo::variables_map options;
    bpo::store(bpo::command_line_parser(argc, argv)
               .options(desc).positional(pos_desc).run(), options);
    bpo::notify(options);

    if (options.count("help"))
    {
        std::cerr << desc << std::endl;
        return 0;
    }
    else if (!options.count("input-file"))
    {
        std::cerr << "No input file specified." << std::endl;
        return 1;
    }
    else if (!options.count("output-file"))
    {
        std::cerr << "No output file specified" << std::endl;
        return 1;
    }
    if (options.count("polynomials"))
    {
        typedef std::string::const_iterator iter_t;
        std::vector<std::string> polynomials;
        polynomials = options["polynomials"].as<std::vector<std::string> >();

        for (std::vector<std::string>::const_iterator it=polynomials.begin();
             it != polynomials.end(); ++it)
        {
            expressions.push_back(ExpressionMachine::code_t());
            Expression<iter_t> expr(expressions.back());
            std::string::const_iterator iter=it->begin(), end=it->end();
            try
            {
                bs::qi::phrase_parse(iter, end, expr, bs::ascii::space);
            }
            catch (const bs::qi::expectation_failure<iter_t>&)
            {
                std::cerr << "Parsing of expression " << *it << " failed."
                          << std::endl;
                return 1;
            }
        }
    }

    Song song;

    // Supported images
    typedef boost::mpl::vector<bg::gray8_image_t,
                               bg::rgb8_image_t,
                               bg::rgba8_image_t> images_t;

    // Load input image
    bg::any_image<images_t> img;
    try
    {
        png_read_image(options["input-file"].as<std::string>(), img);
    }
    catch (const std::ios_base::failure&)
    {
        std::cerr << "Could not load input file." << std::endl;
        return 1;
    }
    // Convert any_image to RGB-8 image
    bg::rgb8_image_t rgb_image(img.dimensions());
    bg::copy_and_convert_pixels(
        bg::color_converted_view<bg::rgb8_pixel_t>(bg::const_view(img)),
        bg::view(rgb_image)
    );
    // Convert
    short note_breaks[12] = {0, 21, 42, 63, 84, 105, 126,
                            147, 168, 189, 210, 231};
    // c major, 2 octaves
    int notes[14] = {60, 62, 64, 65, 67, 69, 71, 72, 74, 75, 79, 81, 83, 85};
    RangeMap<short, int> note_map(&note_breaks[0], &note_breaks[11],
                                  &notes[0], &notes[13]);
    if (options.count("range"))
        range_convert_image(bg::const_view(rgb_image), song, ntracks,
                            note_map);
    else
        polynomial_convert_image(bg::const_view(rgb_image), song,
                                 expressions, note_map);

    song.write_midi(options["output-file"].as<std::string>());

    return 0;
}
