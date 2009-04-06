/*! \file utilities.hpp
some meta programming stuff
*/

#ifndef _std_ext_utilities_
#define _std_ext_utilities_

namespace std_ext {

//! compile time if then else (see [VandervoordeJosuttis, Templates])
template <bool b,
    class T,
    class U>
struct if_then_else
{
    typedef T type;
};

//! spezalitation of std_ext::if_then_else
template <class T, 
    class U>
struct if_then_else<false, T, U>
{
    typedef U type;
};

//! compile time if then else to use with type_to_type (or anything else which provides a type type(def))
template <bool b,
    class T,
    class U>
struct if_then_else_type
{
    typedef typename T::type type;
};

//! spezalitation of std_ext::if_then_else_type
template <class T, 
    class U>
struct if_then_else_type<false, T, U>
{
    typedef typename U::type type;
};

//! maps a value to a type (see [VandervoordeJosuttis, Templates])
template <int i>
struct value_to_type
{
    enum { value = i };
};

//! maps a type to a type (see [VandervoordeJosuttis, Templates])
template <class T>
struct type_to_type
{
    typedef T type;
};

//! the same as std_ext::type_to_type
template <class T>
struct result_wrapper
{
    typedef typename type_to_type<T>::type type;
};

} // namespace std_ext

#endif // include guard
