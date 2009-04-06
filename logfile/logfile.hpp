// logfile.hpp, v1.0
// 

#ifndef _logfile_hpp_
#define _logfile_hpp_

#include <fstream>
#include <std_ext/ctime.hpp>

// logging-class based on std::ofstream
template<class C, 
    class TFN = std_ext::time_fns<C> >
class basic_logfile {
public:
    // some typedefs
    typedef C char_t;
    typedef basic_logfile<C> my_t;
    typedef TFN time_fns_t;

    typedef std::basic_ofstream<char_t> ofstream;

    // constructors
    basic_logfile(const char* sz, std::ios::openmode om = std::ios::app) : m_ofs(sz, om) {
        this->startup();
    }   

    // destructor
    ~basic_logfile() {
        this->end();
    }

    // operator << for each type!
    // an operator <<(ofstream, T) or ofstream::operator<<(T) must exist
    template<class T>
    my_t& operator<<(const T& t) {
        char_t sz[16] = { '\0' }; time_fns_t::time_t tm = time_fns_t::time(0);
        time_fns_t::strftime(sz, 16, "%H:%M:%S", time_fns_t::localtime(&tm));

        this->m_ofs << sz << this->m_ofs.widen('\t') << t << this->m_ofs.widen('\n');

        return (*this);
    }

    // write
    // calls operator <<
    template<class T>
    void write(const T& t) {
        (*this) << t;
    }

    // flush
    void flush() {
        this->m_ofs.flush();
    }

    // good
    bool good() const {
        return this->m_ofs.good();
    }

    // fail
    bool fail() const {
        return this->m_ofs.fail();
    }

private:
    // startup
    inline void startup() {
        (*this) << "*** begin logging! ***";
    }

    // end
    inline void end() {
        (*this) << "*** end logging! ***\n";
    }

    // forbid copying and assigning
    basic_logfile(const my_t&);
    my_t& operator=(const my_t&);

    // ofstream representation
    ofstream m_ofs;
};

typedef basic_logfile<char, std_ext::time_fns<char> > logfile;
typedef basic_logfile<wchar_t, std_ext::time_fns<wchar_t> > wlogfile;

#endif
