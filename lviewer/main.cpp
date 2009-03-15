//
// A small LSystem viewer, written 2008 by Andy S.
//

#include <iostream>
#include <map>
#include <string>
#include <vector>

#include <cairomm/context.h>
#include <cairomm/refptr.h>
#include <gtkmm.h>
#include <libglademm.h>

#include <boost/bind.hpp>
#include <boost/function.hpp>
#include <boost/spirit/core.hpp>
#include <boost/spirit/actor.hpp>
#include <boost/spirit/utility.hpp>
namespace bs = boost::spirit;


const float PI = 3.14159265358979323846;


//
// The Lindenmayer System
//

class LSystem
{
public:
    LSystem(const std::string& axiom, const std::map<char,std::string>& rules);

    typedef std::pair<char, int> Letter;
    unsigned int depth;
    void iterate(const unsigned int n=1);

    std::vector<Letter> word() { return word_; };
protected:
    typedef std::map<char, std::string> RulesMap;
    RulesMap rules_;
    std::vector<Letter> word_;
};

LSystem::LSystem(const std::string& axiom,
                 const std::map<char, std::string>& rules)
    : depth(0), rules_(rules)
{
    for (std::string::const_iterator it=axiom.begin(); it != axiom.end(); ++it)
        word_.push_back(Letter(*it, 0));
}

void LSystem::iterate(const unsigned int n)
{
    for (unsigned int i=0; i != n; ++i)
    {
        ++depth;
        std::vector<Letter> current_word;
        current_word.swap(word_);
        for (std::vector<Letter>::const_iterator it=current_word.begin();
             it != current_word.end(); ++it)
        {
            RulesMap::const_iterator rule = rules_.find(it->first);
            if (rule != rules_.end())
                for (std::string::const_iterator rule_it=rule->second.begin();
                     rule_it != rule->second.end(); ++rule_it)
                    word_.push_back(Letter(*rule_it, depth));
            else
                word_.push_back(*it);
        }
    }
}


bool parse_lsystem_desc(const std::string& desc, int& iterations, float& angle,
                        std::string& axiom, std::map<char, std::string>& rules)
{
    std::pair<char, std::string> rule;
    // Grammar
    bs::chset<> letter_r = bs::chset<>(bs::anychar_p) - bs::chset<>(",)");
    bs::rule<> word_r = +letter_r;
    bs::rule<> production_r = (
            letter_r[bs::assign_a(rule.first)] >> "->" >>
            word_r[bs::assign_a(rule.second)]
    )[bs::insert_at_a(rules, rule.first, rule.second)];
    bs::rule<> lsystem_r = '(' >>
        bs::int_p[bs::assign_a(iterations)] >> ',' >>
        bs::real_p[bs::assign_a(angle)] >> ',' >>
        word_r[bs::assign_a(axiom)] >> ',' >>
        '(' >> production_r >> *(',' >> production_r) >> ')' >>
    ')';
    bs::parse_info<> info = bs::parse(desc.c_str(), lsystem_r, bs::space_p);
    return info.full;
}



//
// LSystem drawing widget
//

class LSystemDrawingArea : public Gtk::DrawingArea
{
    Glib::Property<float> property_d_;
    Glib::Property<float> property_delta_;
    Glib::Property<std::vector<LSystem::Letter> > property_word_;
protected:
    typedef const Cairo::RefPtr<Cairo::Context> ContextPtr;
    typedef boost::function<void (ContextPtr, const unsigned int)> Handler;
    typedef std::map<char, Handler> HandlerMap;
    virtual bool on_expose_event(GdkEventExpose* event);
    virtual void on_word_changed();
    HandlerMap handlers_;
    ContextPtr cairo_context();
    Cairo::RefPtr<Cairo::ImageSurface> surface_;
public:
    LSystemDrawingArea();
    virtual ~LSystemDrawingArea() {};
    Glib::PropertyProxy<float> property_d();
    Glib::PropertyProxy<float> property_delta();
    Glib::PropertyProxy<std::vector<LSystem::Letter> > property_word();
    std::vector<std::pair<double, double> > points_;
    void forward(ContextPtr context, unsigned int depth, bool draw);
    void left(ContextPtr context, unsigned int depth);
    void right(ContextPtr context, unsigned int depth);
    void push(ContextPtr context, unsigned int depth);
    void pop(ContextPtr context, unsigned int depth);
};

LSystemDrawingArea::LSystemDrawingArea()
    : Glib::ObjectBase(typeid(LSystemDrawingArea))
    , Gtk::DrawingArea()
    , property_d_(*this, "d", 5)
    , property_delta_(*this, "delta", 45)
    , property_word_(*this, "word", std::vector<LSystem::Letter>())
    , surface_(0)
{
    property_word().signal_changed().connect(
        sigc::mem_fun(*this, &LSystemDrawingArea::on_word_changed)
    );
    // Default handlers
    handlers_['F'] = boost::bind(&LSystemDrawingArea::forward, this,
                                 _1, _2, true);
    handlers_['f'] = boost::bind(&LSystemDrawingArea::forward, this,
                                 _1, _2, false);
    handlers_['+'] = boost::bind(&LSystemDrawingArea::left, this, _1, _2);
    handlers_['-'] = boost::bind(&LSystemDrawingArea::right, this, _1, _2);
    handlers_['['] = boost::bind(&LSystemDrawingArea::push, this, _1, _2);
    handlers_[']'] = boost::bind(&LSystemDrawingArea::pop, this, _1, _2);
}

// Helper function
const LSystemDrawingArea::ContextPtr LSystemDrawingArea::cairo_context()
{
    Glib::RefPtr<Gdk::Window> window = get_window();
    if (window)
        return window->create_cairo_context();
    return ContextPtr(0);
}

void LSystemDrawingArea::forward(ContextPtr context, const unsigned int depth,
                                 bool draw=true)
{
    if (draw)
        context->rel_line_to(0, property_d_.get_value());
    else
        context->rel_move_to(0, property_d_.get_value());
}

void LSystemDrawingArea::left(ContextPtr context, const unsigned int depth)
{
    const float angle = property_delta_.get_value() / 180 * PI;
    context->rotate(angle);
}

void LSystemDrawingArea::right(ContextPtr context, const unsigned int depth)
{
    const float angle = -property_delta_.get_value() / 180 * PI;
    context->rotate(angle);
}

void LSystemDrawingArea::push(ContextPtr context, const unsigned int depth)
{
    double x, y;
    context->get_current_point(x, y);
    points_.push_back(std::pair<double, double>(x, y));
    context->save();
}

void LSystemDrawingArea::pop(ContextPtr context, const unsigned int depth)
{
    std::pair<double, double> point = points_.back();
    points_.pop_back();
    context->stroke();
    context->restore();
    context->move_to(point.first, point.second);
}

Glib::PropertyProxy<float> LSystemDrawingArea::property_d()
{
    return property_d_.get_proxy();
}

Glib::PropertyProxy<float> LSystemDrawingArea::property_delta()
{
    return property_delta_.get_proxy();
}

Glib::PropertyProxy<std::vector<LSystem::Letter> > LSystemDrawingArea::property_word()
{
    return property_word_.get_proxy();
}

bool LSystemDrawingArea::on_expose_event(GdkEventExpose* event)
{
    ContextPtr context = cairo_context();
    if (context && surface_)
    {
        // Only draw the area which must be redrawn
        context->rectangle(event->area.x, event->area.y,
                       event->area.width, event->area.height);
        context->clip();
        context->set_source(surface_, 0, 0);
        context->paint();
    }
    return true;
}

void LSystemDrawingArea::on_word_changed()
{
    // TODO: Use user's size
    Gtk::Allocation allocation = get_allocation();
    const int width = allocation.get_width();
    const int height = allocation.get_height();
    surface_ = Cairo::ImageSurface::create(Cairo::FORMAT_ARGB32, width,
                                           height);
    ContextPtr context = Cairo::Context::create(surface_);
    // Draw the new word
    // Save context
    context->save();
    // Fill background
    context->set_source_rgb(1, 1, 1);
    context->paint();
    // Draw the LSystem
    context->set_source_rgb(0, 1, 0);
    Cairo::Matrix matrix = {1, 0, 0, -1, width / 2, height};
    context->transform(matrix);
    context->begin_new_path();
    context->move_to(0, height / 2);
    std::vector<LSystem::Letter> word = property_word_.get_value();
    for (std::vector<LSystem::Letter>::const_iterator it=word.begin();
         it != word.end(); ++it)
    {
        HandlerMap::const_iterator handler = handlers_.find(it->first);
        if (handler != handlers_.end())
            handler->second(context, it->second);
    }
    context->stroke();
    // Restore context
    context->restore();
}


//
// Main window
//

class MainWindow : public Gtk::Window
{
public:
    MainWindow(BaseObjectType* cobject, const Glib::RefPtr<Gnome::Glade::Xml>& glade_xml);
    virtual ~MainWindow() {};
    Gtk::Entry* lsystementry_;
    LSystemDrawingArea lsystemarea_;

protected:
    virtual void on_button_click();
};

MainWindow::MainWindow(BaseObjectType *cobject,
                       const Glib::RefPtr<Gnome::Glade::Xml>& glade_xml)
    : Gtk::Window(cobject)
{
    // Add lsystem drawing area
    Gtk::Viewport* viewport = 0;
    viewport = glade_xml->get_widget("LSystemViewport", viewport);
    viewport->add(lsystemarea_);
    show_all_children();
    // Bind some widgets to members
    lsystementry_ = glade_xml->get_widget("LSystemEntry", lsystementry_);
    // Connect signals
    Gtk::Button* button = 0;
    button = glade_xml->get_widget("DrawButton", button);
    button->signal_clicked().connect(
        sigc::mem_fun(*this, &MainWindow::on_button_click)
    );
}


void MainWindow::on_button_click()
{
    float angle;
    int iterations;
    std::string axiom;
    std::map<char, std::string> rules;
    if (parse_lsystem_desc(lsystementry_->get_text(),
                           iterations, angle, axiom, rules))
    {
        LSystem lsystem(axiom, rules);
        lsystem.iterate(iterations);
        lsystemarea_.property_delta().set_value(angle);
        lsystemarea_.property_word().set_value(lsystem.word());
        // Force redraw
        lsystemarea_.queue_draw();
    }
    else
    {
        Gtk::MessageDialog dialog(*this, "Konnte die LSystem-Beschreibung "
                                  "nicht parsen.", false, Gtk::MESSAGE_ERROR);
        dialog.run();
    }
}


int main(int argc, char** argv)
{
    Gtk::Main kit(argc, argv);
    // Load the glade file
    Glib::RefPtr<Gnome::Glade::Xml> glade_xml;
#ifdef GLIBMM_EXCEPTIONS_ENABLED
    try
    {
        glade_xml = Gnome::Glade::Xml::create("lp.glade");
    }
    catch (const Gnome::Glade::XmlError& exc)
    {
        std::cerr << exc.what() << std::endl;
        return 1;
    }
#else
    std::auto_ptr<Gnome::Glade::XmlError> error;
    glade_xml = Gnome::Glade::Xml::create("lp.glade", "", "", error);
    if(error.get())
    {
        std::cerr << error->what() << std::endl;
        return 1;
    }
#endif
    
    MainWindow* window = 0;
    window = glade_xml->get_widget_derived("MainWindow", window);
    if (!window)
    {
        std::cerr << "Fatal error." << std::endl;
        return 1;
    }
    kit.run(*window);
    delete window;

#if 0
    // Algae
    std::string axiom("A");
    std::map<char,std::string> rules;
    rules['A'] = "AB";
    rules['B'] = "A";

    LSystem lsystem(axiom, rules);

    std::string word = axiom;
    for (int i=0; i != 10; ++i, word=lsystem.iterate())
        std::cout << "n=" << i << ": " << word << std::endl;
#endif
    return 0;
}

// vim: set sts=4 et sw=4 tw=74 :
