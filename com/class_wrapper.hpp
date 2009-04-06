
#ifndef _COM_CLASS_WRAPPER_HPP_
#define _COM_CLASS_WRAPPER_HPP_

#include <boost/static_assert.hpp>
#include <boost/type_traits.hpp>
#include <std_ext/null.hpp>
#include "refcounter.hpp"

namespace com
{

extern const GUID IID_class_wrapper;    // {3141BC3B-113D-4c29-943F-3530403E7D76}

// class com::class_wrapper
// wrapps class types
template<class T>
class class_wrapper : public refcounter, public T
{
    BOOST_STATIC_ASSERT((!boost::is_base_and_derived<IUnknown, T>::value));
    BOOST_STATIC_ASSERT((boost::is_class<T>::value));
public:
    class_wrapper() : T() {}
    class_wrapper(const T& t) : T(t) {}
    virtual ~class_wrapper() {}

    long __stdcall QueryInterface(REFIID id, void** p)
    {
        if (id == IID_IUnknown || id == IID_class_wrapper)
        {
            *p = this;
            AddRef();

            return S_OK;
        }
        else
        {
            *p = std_ext::nullptr;
            return E_NOINTERFACE;
        }
    }
};

} // namespace com

#endif // _COM_CLASS_WRAPPER_HPP_
