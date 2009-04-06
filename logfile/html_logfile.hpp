// html_logfile.hpp, v1.0
// 

#ifndef _html_logfile_hpp_
#define _html_logfile_hpp_

#include <fstream>
#include <string>
#include <sstream>
#include <std_ext/ctime>

// html-logging-class based on std::ofstream
template<class C, 
    class TFN = std_ext::time_fns<C> >
class basic_html_logfile {
public:
    // some typedefs
    typedef C char_t;
    typedef basic_html_logfile<C> my_t;
    typedef TFN time_fns_t;

    typedef std::basic_ofstream<char_t> ofstream_t;
    typedef std::basic_string<char_t> string_t;
    typedef std::basic_stringstream<char_t> sstream_t;

    // write type enum
    typedef enum __write {
        w_warning,
        w_error,
        w_info
    } write_t;

    // color enum
    typedef enum __color {
        co_default,
        co_red,
        co_blue,
        co_green,

        co_yellow,
        co_grey,
        co_darkgrey,

        co_black,
        co_white
    } color_t;

    // format struct
    typedef struct __format {
        bool bold, italic, underlined;
        unsigned int size;
        color_t color;
    } format_t;

    // constructors
    basic_html_logfile(const char* szFileName, const char_t* szTitle, const char_t* szHeader) 
        : m_ofs(szFileName) {
        this->begin_log(szTitle, szHeader);
    }   

    // destructor
    ~basic_html_logfile() {
        this->end_log();
    }

    // write
    void write(const char_t* sz, write_t w = w_info, const char_t* szFile = 0, const char_t* szFunction = 0, unsigned int uLine = 0) {
        this->begin_line();
        
        // write time
        this->begin_cell();
        this->write_time();
        this->end_cell();

        // write "INFO", "WARNING" or "ERROR"
        this->begin_cell();
        switch (w)
        {
            case w_info:    this->write_formated("INFO", this->m_fmtinfo); break;
            case w_warning: this->write_formated("WARNING", this->m_fmtwarning); break;
            case w_error:   this->write_formated("ERROR", this->m_fmterror); break;
        }
        this->end_cell();

        // write message
        this->begin_cell(550);
        this->write_formated(sz, this->m_fmt);
        this->end_cell();
        
        this->begin_cell();
        if (szFile)
        {
            // add information about file, function and line
            this->write_formated("in ", this->m_fmt);
            this->write_formated(szFile, this->m_fmtfninfo);

            if (szFunction) {
                this->write_formated(", function ", this->m_fmt);
                this->write_formated(szFunction, this->m_fmtfninfo);
            }
            if (uLine) {
                this->write_formated(", on line ", this->m_fmt);
                
                sstream_t ss; ss << uLine;
                this->write_formated(ss.str().c_str(), this->m_fmtfninfo);
            }
        }

        this->end_cell();
        this->end_line();
        this->m_ofs.flush();
    }

    // setformat
    format_t setformat(const format_t& fmt) {
        format_t t = this->m_fmt;
        this->m_fmt = fmt;

        return t;
    }

private:
    // begin_log
    inline void begin_log(const char_t* szTitle, const char_t* szHeader) {
        this->m_fmt.bold = this->m_fmt.italic = this->m_fmt.underlined = false;
        this->m_fmt.size = 3;
        this->m_fmt.color = co_default;

        this->m_fmtinfo.bold = this->m_fmterror.bold = this->m_fmtwarning.bold = true;
        this->m_fmtinfo.underlined = this->m_fmterror.underlined = this->m_fmtwarning.underlined = false;
        this->m_fmtinfo.italic = this->m_fmterror.italic = this->m_fmtwarning.italic = false;
        this->m_fmtinfo.size = this->m_fmterror.size = this->m_fmtwarning.size = 3;
        this->m_fmterror.color = this->m_fmtwarning.color = co_red;
        this->m_fmtinfo.color = co_green;

        this->m_fmtfninfo.bold = this->m_fmttime.bold = false;
        this->m_fmtfninfo.underlined = this->m_fmttime.underlined = false;
        this->m_fmtfninfo.italic = this->m_fmttime.italic = true;
        this->m_fmtfninfo.size = this->m_fmttime.size = 3;
        this->m_fmtfninfo.color = this->m_fmttime.color = co_default;

        this->m_ofs << "<html>\n<head>\n<title>" << szTitle << "</title>\n";
        this->m_ofs << "<meta name=\"generator\" content=\"basic_html_logfile\">\n";
        this->m_ofs << "</head>\n\n<body>\n";

        this->m_ofs << "<p><font size=\"5\">" << this->convert_to_html(szHeader) << "</font></p>\n";

        this->begin_table();
        this->write("begin logging");
    }

    // end_log
    inline void end_log() {
        this->write("end logging");
        this->end_table();
        
        this->m_ofs << "</body>\n</html>\n";
    }

    // begin_line
    inline void begin_line() {
        this->m_ofs << "<tr>\n";
    }

    // end_line
    inline void end_line() {
        this->m_ofs << "</tr>\n";
    }

    // begin_cell
    inline void begin_cell(unsigned int u = 0) {
        if (!u) this->m_ofs << "<td>\n";
        else    this->m_ofs << "<td width=\"" << u << "\">\n";
    }

    // end_cell
    inline void end_cell() {
        this->m_ofs << "</td>\n";
    }

    // begin_table
    inline void begin_table() {
        this->m_ofs << "<table cellspacing=\"3\" cellpadding=\"3\" width=\"950\">\n";
    }

    // end_table
    inline void end_table() {
        this->m_ofs << "</table>\n";
    }

    // convert_to_html
    // replace \n and \t with <br> and 4 (non breakable) white spaces
    string_t convert_to_html(const char_t* sz) {
        string_t str; str.reserve(std::char_traits<char_t>::length(sz) + 1);
        
        while (*sz)
        {
            if (*sz == '\n')        str += "<br>";
            else if (*sz == '\t')   str += "&nbsp;&nbsp;&nbsp;&nbsp;";
            else                    str += *sz;

            sz++;
        }

        return str;
    }

    // write_time
    inline void write_time() {
        char_t sz[16] = { '\0' }; time_fns_t::time_t t = time_fns_t::time(0);
        time_fns_t::strftime(sz, 16, "%H:%M:%S", time_fns_t::localtime(&t));
        this->write_formated(sz, this->m_fmttime);
    }

    // write_formated
    void write_formated(const char_t* sz, const format_t& fmt) {
        // set format tags
        if (fmt.bold)       this->m_ofs << "<b>";
        if (fmt.italic)     this->m_ofs << "<i>";
        if (fmt.underlined) this->m_ofs << "<u>";

        this->m_ofs << "<font size=\"" << fmt.size << "\"";
        if (fmt.color != co_default)
        {
            this->m_ofs << " color=\"";
            switch (fmt.color)
            {
                case co_red:        this->m_ofs << "#ff0000";   break;
                case co_green:      this->m_ofs << "#008000";   break; // #00ff00
                case co_blue:       this->m_ofs << "#0000ff";   break;
                
                case co_yellow:     this->m_ofs << "#ffff00";   break;
                case co_grey:       this->m_ofs << "#0c0c0c";   break;
                case co_darkgrey:   this->m_ofs << "#808080";   break;

                case co_black:      this->m_ofs << "#000000";   break;
                case co_white:      this->m_ofs << "#ffffff";   break;
            }
            this->m_ofs << "\"";
        }
        this->m_ofs << ">";

        // write string
        this->m_ofs << this->convert_to_html(sz);

        // close format tags
        this->m_ofs << "</font>";

        if (fmt.underlined) this->m_ofs << "</u>";
        if (fmt.italic)     this->m_ofs << "</i>";
        if (fmt.bold)       this->m_ofs << "</b>";
    }

    // forbid copying and assigning
    basic_html_logfile(const my_t&);
    my_t& operator=(const my_t&);

    // ofstream_t representation
    ofstream_t m_ofs;
    
    // format definitions
    format_t m_fmt;         // format

    format_t m_fmttime;     // time format
    format_t m_fmtwarning;  // warning format
    format_t m_fmterror;    // error format
    format_t m_fmtinfo;     // info format
    format_t m_fmtfninfo;   // function info format
};

typedef basic_html_logfile<char, std_ext::time_fns<char> > html_logfile;
typedef basic_html_logfile<wchar_t, std_ext::time_fns<wchar_t> > html_wlogfile;

#endif
