
#ifndef _std_ext_typeinfo_
#define _std_ext_typeinfo_

#include <std_ext/null.hpp>
#include <std_ext/utilities.hpp>

namespace std_ext {
namespace detail {

// pointer traits
template<class U>
struct pointer_traits
{
    enum { is_pointer = false };
    enum { is_ptm = false };
    typedef U* pointer_t;
    typedef U base_t;
};

// specialization for U&
template<class U>
struct pointer_traits<U&>
{
    enum { is_pointer = false };
    enum { is_ptm = false };
    typedef null_t pointer_t; // there are no U&*
    typedef null_t base_t;
};
    
template<class U>
struct pointer_traits<U*>
{
    enum { is_pointer = true };
    enum { is_ptm = false };
    typedef U* pointer_t;
    typedef U base_t;
};

template<class U>
struct pointer_traits<U* const>
{
    enum { is_pointer = true };
    enum { is_ptm = false };
    typedef U* const pointer_t;
    typedef U base_t;
};

template<class U, class V>
struct pointer_traits<U V::*>
{
    enum { is_pointer = true };
    enum { is_ptm = true };
    typedef U V::* pointer_t;
    typedef U base_t;
};

template<class U, class V>
struct pointer_traits<U V::* const>
{
    enum { is_pointer = true };
    enum { is_ptm = true };
    typedef U V::* const pointer_t;
    typedef U base_t;
};

// reference traits
template<class U>
struct reference_traits
{
    enum { is_reference = false };
    typedef U& reference_t;
    typedef U base_t;
};

template<>
struct reference_traits<void>
{
    enum { is_reference = false };
    typedef null_t reference_t;
    typedef null_t base_t;
};

template<class U>
struct reference_traits<U[]>
{
    enum { is_reference = false };
    typedef null_t reference_t; // there are no U[]&
    typedef null_t base_t;
};

template<class U>
struct reference_traits<U&>
{
    enum { is_reference = true };
    typedef U& reference_t; // there are no U&&
    typedef U base_t;
};

// array traits
template<class U>
struct array_traits
{
    enum { is_array = false };
};

template<class U, int N>
struct array_traits<U[N]>
{
    enum { is_array = true };
};

template<class U>
struct array_traits<U[]>
{
    enum { is_array = true };
};

// const traits
template<class U>
struct const_traits
{
    enum { is_const = false };
    typedef U nonconst_type_t;
    typedef const U const_type_t;
};

template<class U>
struct const_traits<const U>
{
    enum { is_const = true };
    typedef U nonconst_type_t;
    typedef const U const_type_t;
};

// volatile traits
template<class U>
struct volatile_traits
{
    enum { is_volatile = false };
    typedef U nonvolatile_type_t;
    typedef volatile U volatile_type_t;
};

template<class U>
struct volatile_traits<volatile U>
{
    enum { is_volatile = true };
    typedef U nonvolatile_type_t;
    typedef volatile U volatile_type_t;
};

// qualified type
template<class U>
struct qualified_traits
{
    enum { is_qualified = false };
    typedef U nonqualified_type_t;
};

template<class U>
struct qualified_traits<volatile U>
{
    enum { is_qualified = true };
    typedef U nonqualified_type_t;
};

template<class U>
struct qualified_traits<const U>
{
    enum { is_qualified = true };
    typedef U nonqualified_type_t;
};

template<class U>
struct qualified_traits<const volatile U>
{
    enum { is_qualified = true };
    typedef U nonqualified_type_t;
};


// fundamental traits
template<class U>
struct fundamental_traits
{
    enum { is_fundamental = false };
};

#define FT_MAKE_FUNDAMENTAL(U) \
    template<> \
    struct fundamental_traits<U> \
    { \
        enum { is_fundamental = true }; \
    };

FT_MAKE_FUNDAMENTAL(bool)

FT_MAKE_FUNDAMENTAL(char)
FT_MAKE_FUNDAMENTAL(signed char)
FT_MAKE_FUNDAMENTAL(unsigned char)

FT_MAKE_FUNDAMENTAL(wchar_t)

FT_MAKE_FUNDAMENTAL(short)
// FT_MAKE_FUNDAMENTAL(signed short)
FT_MAKE_FUNDAMENTAL(unsigned short)

FT_MAKE_FUNDAMENTAL(int)
// FT_MAKE_FUNDAMENTAL(signed int)
FT_MAKE_FUNDAMENTAL(unsigned int)

FT_MAKE_FUNDAMENTAL(long)
// FT_MAKE_FUNDAMENTAL(signed long)
FT_MAKE_FUNDAMENTAL(unsigned long)

FT_MAKE_FUNDAMENTAL(float)
FT_MAKE_FUNDAMENTAL(double)
FT_MAKE_FUNDAMENTAL(long double)

#undef FT_MAKE_FUNDAMENTAL

// class traits
template<class U>
struct class_traits
{
private:
    typedef struct { char c[1]; } one_t;
    typedef struct { char c[2]; } two_t;

    // test after [VandervoordeJosuttis, Templates]
    template<class V> static one_t test(int V::*);
    template<class V> static two_t test(...);

public:
    enum { is_class = sizeof(test<U>(0)) == sizeof(one_t) };
};

}

template<class T>
struct type_traits
{
    // pointer
    enum { is_pointer = detail::pointer_traits<T>::is_pointer };
    enum { is_memberpointer = detail::pointer_traits<T>::is_ptm };
    typedef typename detail::pointer_traits<T>::pointer_t pointer_t;
    typedef typename detail::pointer_traits<T>::base_t pointer_base_t;

    // reference
    enum { is_reference = detail::reference_traits<T>::is_reference };
    typedef typename detail::reference_traits<T>::reference_t reference_t;
    typedef typename detail::reference_traits<T>::base_t reference_base_t;

    // array
    enum { is_array = detail::array_traits<T>::is_array };

    // const
    enum { is_const = detail::const_traits<T>::is_const };
    typedef typename detail::const_traits<T>::nonconst_type_t nonconst_type_t;
    typedef typename detail::const_traits<T>::const_type_t const_type_t;

    // volatile
    enum { is_volatile = detail::volatile_traits<T>::is_volatile };
    typedef typename detail::volatile_traits<T>::nonvolatile_type_t nonvolatile_type_t;
    typedef typename detail::volatile_traits<T>::volatile_type_t volatile_type_t;

    // qualified
    enum { is_qualified = detail::qualified_traits<T>::is_qualified };
    typedef typename detail::qualified_traits<T>::nonqualified_type_t nonqualified_type_t;

    // fundamental, class, enum
    enum { is_fundamental = detail::fundamental_traits<nonqualified_type_t>::is_fundamental };
    enum { is_class = detail::class_traits<T>::is_class };
    enum { is_enum = !is_fundamental && !is_pointer && !is_memberpointer && !is_reference && !is_array && !is_class };

    // argument
    typedef typename if_then_else<is_fundamental || is_enum, T, const reference_t>::result argument_t;
};

} // namespace std_ext

#endif // include guard
