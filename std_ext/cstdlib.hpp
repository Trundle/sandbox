/*! \file cstdlib.hpp
some <cstdlib> extensions   ...
*/

#ifndef _std_ext_cstdlib_
#define _std_ext_cstdlib_

#include <cstdlib>
#include <limits>

// some non compliant headers may define min and max macros
#ifdef min
#undef min
#endif

#ifdef max
#undef max
#endif

namespace std_ext {

//! generate a random number in the range of [min, max] (by Wledge/Trent/wraith)
//! \param min the range's beginning
//! \param max the range's end
//! \return a random number in the range of [min, max]
template<class T> inline T rand_min_max(T min, 
                                        T max) 
{
    return static_cast<T>(std::rand() % static_cast<int>(max - min) + min);
} 

//! generates a random number in the range of [numeric_limits<T>::min(), numeric_limits<T>::max()]
//! \return a random number in the range of [numeric_limits<T>::min(), numeric_limits<T>::max()]
template<class T> inline T rand_limits()
{
    return rand_min_max(std::numeric_limits<T>::min(), std::numeric_limits<T>::max());
}

} // namespace std_ext

#endif // include guard
