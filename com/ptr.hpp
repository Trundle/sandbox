
#ifndef _COM_PTR_HPP_
#define _COM_PTR_HPP_

#include <boost/static_assert.hpp>
#include <boost/type_traits.hpp>
#include <std_ext/null.hpp>

namespace com
{

// function addref
template<class T> 
unsigned long checked_addref(T* t)
{
    BOOST_STATIC_ASSERT((boost::is_base_and_derived<IUnknown, T>::value));

    if (t)  return t->AddRef();
    else    return 0;
}

// function release
template<class T> 
unsigned long checked_release(T* p)
{
    BOOST_STATIC_ASSERT((boost::is_base_and_derived<IUnknown, T>::value));

    if (p)  return p->Release();
    else    return 0;
}

// class com::ptr
// smart pointer for COM objects
template<class T>
class ptr
{
    BOOST_STATIC_ASSERT((boost::is_base_and_derived<IUnknown, T>::value));
public:
    typedef T stored_type;
    typedef T* storage_type;
private:
    storage_type data_;
public:
    // c'tor
    ptr(storage_type p = std_ext::nullptr) : data_(p) {}

    // copy c'tor
    ptr(const ptr<T>& rhs)  : data_(rhs.data_)
    {
        checked_addref(data_);
    }

    // d'tor
    ~ptr()
    {
        checked_release(data_);
    }

    // operator=
    ptr<T>& operator=(const ptr<T>& rhs)
    {
        reset(rhs.data_);
        checked_addref(data_);

        return *this;
    }

    // get
    storage_type get() const
    {
        return data_;
    }

    // reset
    void reset(storage_type p = std_ext::nullptr)
    {
        checked_release(data_);
        data_ = p;
    }

    // release
    storage_type release()
    {
        storage_type t = data_;
        data_ = std_ext::nullptr;

        return t;
    }

    // operator*
    stored_type& operator*()
    {
        return *data_;
    }

    const stored_type& operator*() const
    {
        return *data_;
    }

    // operator->
    storage_type operator->()
    {
        return data_;
    }

    const storage_type operator->() const
    {
        return data_;
    }
};

} // namespace com

#endif // _COM_PTR_HPP_
