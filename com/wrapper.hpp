
#ifndef _COM_WRAPPER_HPP_
#define _COM_WRAPPER_HPP_

#include <boost/static_assert.hpp>
#include <boost/type_traits.hpp>
#include <std_ext/null.hpp>
#include <std_ext/utilities.hpp>
#include "class_wrapper.hpp"
#include "fundamental_wrapper.hpp"
#include "ptr.hpp"

namespace com
{

template<class T>
ptr<fundamental_wrapper<T> > create_wrapped_fundamental(const T& t = T())
{
    BOOST_STATIC_ASSERT((boost::is_fundamental<T>::value));
    return ptr<fundamental_wrapper<T> >(new fundamental_wrapper<T>(t));
}

template<class T>
ptr<class_wrapper<T> > create_wrapped_class(const T& t = T())
{
    BOOST_STATIC_ASSERT((boost::is_class<T>::value));
    return ptr<class_wrapper<T> >(new class_wrapper<T>(t));
}

template<class T>
class wrapper_helper
{
    BOOST_STATIC_ASSERT((!boost::is_base_and_derived<IUnknown, T>::value));
    BOOST_STATIC_ASSERT((boost::is_fundamental<T>::value || boost::is_class<T>::value));
public:
    typedef typename std_ext::if_then_else_result<(boost::is_fundamental<T>::value), 
        std_ext::result_wrapper<fundamental_wrapper<T> >,
        std_ext::result_wrapper<class_wrapper<T> > >::result result;
};

template<class T>
ptr<typename wrapper_helper<T>::result> create_wrapped(const T& t = T())
{
    return typename ptr<wrapper_helper<T>::result>(new wrapper_helper<T>::result(t));
};

} // namespace com

#endif // _COM_WRAPPER_HPP_
