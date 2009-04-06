
#ifndef _COM_FUNDAMENTAL_WRAPPER_HPP_
#define _COM_FUNDAMENTAL_WRAPPER_HPP_

#include <boost/static_assert.hpp>
#include <boost/type_traits.hpp>
#include <std_ext/null.hpp>
#include "refcounter.hpp"

namespace com
{

extern const GUID IID_fundamental_wrapper;  // {7E2EB07A-3203-433b-9406-3E10EF0BD3AF}

// class com::fundamental_wrapper
// wraps fundamental types
template<class T>
class fundamental_wrapper : public refcounter
{
    BOOST_STATIC_ASSERT((boost::is_fundamental<T>::value));

    T t_;
public:
    fundamental_wrapper() : t_(T()) {}
    fundamental_wrapper(const T& t) : t_(t) {}
    virtual ~fundamental_wrapper() {}

    long __stdcall QueryInterface(REFIID id, void** p)
    {
        if (id == IID_IUnknown || id == IID_fundamental_wrapper)
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

    // T cast operators
    operator T&()
    {
        return t_;
    }

    operator const T&() const
    {
        return t_;
    }
};

} // namespace com

#endif // _COM_FUNDAMENTAL_WRAPPER_HPP_
