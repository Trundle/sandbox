/*! \file vector.hpp
some <vector> extensions    ...
*/

#ifndef _std_ext_vector_hpp_
#define _std_ext_vector_hpp_

#include <vector>
#include <cassert>

namespace std_ext {

//! lets a vector shrink to a minimum size (see [Sutter, MExceptionalC++])
//! \param vec the vector
template<class T, class U>
void shrink_vector(std::vector<T, U>& vec)
{
    std::vector<T, U>(vec).swap(vec);
}

// really clears a vector (see [Sutter, MExceptionalC++])
//! \param vec the vector
template<class T, class U>
void clear_vector(std::vector<T, U>& vec)
{
    std::vector<T, U>().swap(vec);
}

} // namespace std_ext

#endif // include guard
