
#ifndef _std_ext_ctime_
#define _std_ext_ctime_

#include <ctime>

namespace std_ext {

// time_fns structure and its specialications for char and wchar_t
struct time_fns_base
{
	typedef std::clock_t clock_t;
	typedef std::size_t size_t;
	typedef std::time_t time_t;
	typedef std::tm tm_t;

	static clock_t clock() {
		return std::clock();
	}

	static double difftime(time_t t1, time_t t2) {
		return std::difftime(t1, t2);
	}

	static tm_t* gmtime(const time_t* p) {
		return std::gmtime(p);
	}

	static tm_t* localtime(const time_t* p) {
		return std::localtime(p);
	}

	static time_t mktime(tm_t* p) {
		return std::mktime(p);
	}

	static time_t time(time_t* p) {
		return std::time(p);
	}
};

template <class C> 
struct time_fns : time_fns_base {};

template<>
struct time_fns<char> : time_fns_base
{
	typedef char char_t;

	static char_t* asctime(const tm* p) {
		return std::asctime(p);
	}

	static char_t* ctime(const time_t* p) {
		return std::ctime(p);
	}

	static char_t* strtime(char_t* p) {
		return _strtime(p);
	}

	static size_t strftime(char_t* p1, size_t s, const char_t* p2, const tm* p3) {
		return std::strftime(p1, s, p2, p3);
	}
};

template<>
struct time_fns<wchar_t>
{
	typedef wchar_t char_t;

	static char_t* asctime(const tm* p) {
		return _wasctime(p);
	}

	static char_t* ctime(const time_t* p) {
		return _wctime(p);
	}

	static char_t* strtime(char_t* p) {
		return _wstrtime(p);
	}

	static size_t strftime(char_t* p1, size_t s, const char_t* p2, const tm* p3) {
		return wcsftime(p1, s, p2, p3);
	}
};

} // namespace std_ext

#endif // include guard
