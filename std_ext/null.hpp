
#ifndef _std_ext_null_
#define _std_ext_null_

namespace std_ext {

// nullptr
//
// a null-pointer class (see [Meyers, EffectiveC++], Item 25 and [Sutter, MAAN])
const class 
{
    // not addressable
    void operator&() const;

public:
    // return a null-pointer
    template<class T>
    operator T*() const {
        return 0;
    }

    // return a null-pointer to an element
    template<class C, class T>
    operator T C::*() const {
        return 0;
    }
} nullptr;

// undefined type
struct null_t {};

} // namespace std_ext

#endif // include guard
