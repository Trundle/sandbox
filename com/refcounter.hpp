
#ifndef _COM_REFCOUNTER_HPP_
#define _COM_REFCOUNTER_HPP_

#define COM_NO_WINDOWS_H
#include <unknwn.h>

namespace com
{

// class com::refcounter
// implements AddRef(), Release() of IUnknown
// special feature: GetRefs() ;-)
class refcounter : public IUnknown
{
    unsigned long refs_;
public:
    refcounter() : refs_(1) {}
    virtual ~refcounter() {}

    // IUnkown functions
    unsigned long __stdcall AddRef()
    {
        return ++refs_;
    }

    unsigned long __stdcall Release()
    {
        if (--refs_ == 0)   
        {
            delete this;
            return 0;
        }
        else    return refs_;
    }

    unsigned long GetRefs() const
    {
        return refs_;
    }
};

} // namespace com

#endif // _COM_REFCOUNTER_HPP_
