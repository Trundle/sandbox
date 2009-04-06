/*! \file vector.hpp
some <string> extensions    ...
*/

#ifndef _std_ext_string_hpp_
#define _std_ext_string_hpp_

#include <algorithm>
#include <cctype>
#include <cwctype>
#include <functional>
#include <string>
#include <iostream>

namespace std_ext
{

//! extended std::char_traits template
template<class C>
struct char_traits : std::char_traits<C> {};

//! char spezilation of std_ext::char_traits
template<>
struct char_traits<char> : public std::char_traits<char>
{
    typedef std::char_traits<char> my_base;

    static bool isalnum(const my_base::char_type& c)
    {
        return (std::isalnum(c) != 0);
    }

    static bool isalpha(const my_base::char_type& c)
    {
        return (std::isalpha(c) != 0);
    }

    static bool iscntrl(const my_base::char_type& c)
    {
        return (std::iscntrl(c) != 0);
    }

    static bool isdigit(const my_base::char_type& c)
    {
        return (std::isdigit(c) != 0);
    }

    static bool isgraph(const my_base::char_type& c)
    {
        return (std::isgraph(c) != 0);
    }

    static bool islower(const my_base::char_type& c)
    {
        return (std::islower(c) != 0);
    }

    static bool isprint(const my_base::char_type& c)
    {
        return (std::isprint(c) != 0);
    }

    static bool ispunct(const my_base::char_type& c)
    {
        return (std::ispunct(c) != 0);
    }

    static bool isspace(const my_base::char_type& c)
    {
        return (std::isspace(c) != 0);
    }

    static bool isupper(const my_base::char_type& c)
    {
        return (std::isupper(c) != 0);
    }

    static bool isxdigit(const my_base::char_type& c)
    {
        return (std::isxdigit(c) != 0);
    }
};

//! wchar_t spezilation of std_ext::char_traits
template<>
struct char_traits<wchar_t> : public std::char_traits<wchar_t>
{
    typedef std::char_traits<wchar_t> my_base;

    static bool isalnum(const my_base::char_type& c)
    {
        return (std::iswalnum(c) != 0);
    }

    static bool isalpha(const my_base::char_type& c)
    {
        return (std::iswalpha(c) != 0);
    }

    static bool iscntrl(const my_base::char_type& c)
    {
        return (std::iswcntrl(c) != 0);
    }

    static bool isdigit(const my_base::char_type& c)
    {
        return (std::iswdigit(c) != 0);
    }

    static bool isgraph(const my_base::char_type& c)
    {
        return (std::iswgraph(c) != 0);
    }

    static bool islower(const my_base::char_type& c)
    {
        return (std::iswlower(c) != 0);
    }

    static bool isprint(const my_base::char_type& c)
    {
        return (std::iswprint(c) != 0);
    }

    static bool ispunct(const my_base::char_type& c)
    {
        return (std::iswpunct(c) != 0);
    }

    static bool isspace(const my_base::char_type& c)
    {
        return (std::iswspace(c) != 0);
    }

    static bool isupper(const my_base::char_type& c)
    {
        return (std::iswupper(c) != 0);
    }

    static bool isxdigit(const my_base::char_type& c)
    {
        return (std::iswxdigit(c) != 0);
    }
};

// is_space functor
// using std_ext::char_traits instead of std::char_traits, because std::char_traits doesn't offer an isspace function
template<class C, class T = std_ext::char_traits<C> >
struct is_space : public std::unary_function<C, bool>
{
    typedef std::unary_function<C, bool> my_base;

    bool operator()(const typename my_base::argument_type& c) const
    {
        return T::isspace(c);
    }
};

//! strips white spaces from the end of a string
//! \param str the string
//! \returns the stripped string
template<class C, class T, class A>
std::basic_string<C, T, A> rtrim(const std::basic_string<C, T, A>& str)
{
    typedef std::basic_string<C, T, A> string;

    typename string::const_reverse_iterator it = std::find_if(str.rbegin(), str.rend(), std::not1(is_space<C>()));
    if (it == str.rend())   return string();
    else                    return string(str.begin(), it.base());
}

//! strips white spaces from the beginning of a string
//! \param str the string
//! \returns the stripped string
template<class C, class T, class A>
std::basic_string<C, T, A> ltrim(const std::basic_string<C, T, A>& str)
{
    typedef std::basic_string<C, T, A> string;

    typename string::const_iterator it = std::find_if(str.begin(), str.end(), std::not1(is_space<C>()));
    if (it == str.end())    return string();
    else                    return string(it, str.end());
}

//! strips white spaces from the beginning and end of a string
//! \param str the string
//! \returns the stripped string
template<class C, class T, class A>
std::basic_string<C, T, A> trim(const std::basic_string<C, T, A>& str)
{
    return ltrim(rtrim(str));
}

} // namespace std_ext

#endif // include guard
