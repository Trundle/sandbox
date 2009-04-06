/*! \file cmath.hpp
some <cmath> extensions ...
*/

#ifndef _std_ext_cmath_hpp_
#define _std_ext_cmath_hpp_

#include <std_ext/utilities.hpp>

namespace std_ext {

namespace detail {

// implementation of ct_pow
template<int i,
    int e>
struct pow_impl
{
    enum { value = pow_impl<i, e-1>::value * i };
};

template<int i>
struct pow_impl<i, 0>
{
    enum { value = 1 };
};

// implementation of ct_root
template<int i,
    int r = 2,
    int j = 1>
struct root_impl
{
    typedef typename if_then_else<(pow_impl<j, r>::value < i), root_impl<i, r, j+1>, value_to_type<j> >
        ::result res;
    enum { value = res::value };
};

// implementation of ct_fac
template<int i>
struct fac_impl
{
    enum { value = fac_impl<i-1>::value * i };
};

template<>
struct fac_impl<0>
{
    enum { value = 1 };
};

} // namespace detail

//! compile time pow for integer constants
template<int i,
    int e>
struct ct_pow
{
    enum { value = detail::pow_impl<i, e>::value };
};

//! compile time root for integer constants
template<int i,
    int r>
struct ct_root
{
    enum { value = detail::root_impl<i, r>::value };
};

//! compile time square root for integer constants
template<int i>
struct ct_sqrt
{
    enum { value = ct_root<i, 2>::value };
};

//! compile time faculty for integer constants
template<int i>
struct ct_fac
{
    enum { value = detail::fac_impl<i>::value };
};

//! run time faculty
inline unsigned int fac(unsigned int i)
{
    int j = 1;
    for (; i > 0; --i)
        j *= i;

    return j;
}

} // namespace std_ext

#endif // include guard
