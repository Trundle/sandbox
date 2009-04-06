
#ifndef _getter_setter_policies_hpp_
#define _getter_setter_policies_hpp_

#include <boost/type_traits/add_const.hpp>
#include <boost/type_traits/add_reference.hpp>
#include <algorithm>

namespace gs
{
namespace policies
{
using std::swap;

template<class T>
struct default_policy
{
    typedef T value_type;
    typedef typename boost::add_reference<value_type>::type reference_type;
    typedef typename boost::add_reference<typename boost::add_const<value_type>::type>::type const_reference_type;

    typedef const_reference_type read_return_type;
    typedef value_type write_return_type;
    typedef value_type write_argument_type;
    typedef const_reference_type constructor_argument_type;

    static value_type on_construct()
    {
        return value_type();
    }

    static constructor_argument_type on_construct(constructor_argument_type val)
    {
        return val;
    }

    static constructor_argument_type on_copy_construct(constructor_argument_type val)
    {
        return val;
    }

    static read_return_type on_read(const_reference_type val)
    {
        return val;
    }

    static write_return_type on_write(reference_type val, write_argument_type new_val)
    {
        swap(val, new_val);
        return new_val;
    }
};

template<class T>
struct read_only
{
    struct null_type {};

    typedef typename boost::add_const<T>::type value_type;
    typedef null_type reference_type;
    typedef typename boost::add_reference<typename boost::add_const<T>::type>::type const_reference_type;

    typedef const_reference_type read_return_type;
    typedef null_type write_return_type;
    typedef null_type write_argument_type;
    typedef const_reference_type constructor_argument_type;

    static value_type on_construct();

    static constructor_argument_type on_construct(constructor_argument_type val)
    {
        return val;
    }

    static constructor_argument_type on_copy_construct(constructor_argument_type val)
    {
        return val;
    }

    static read_return_type on_read(const_reference_type val)
    {
        return val;
    }

    static write_return_type on_write(reference_type val, write_argument_type new_val);
};

}
}

#endif
