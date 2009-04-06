/*! \file algorithm.hpp
some <algorithm> extensions ...
*/

#ifndef _std_ext_algorithm_hpp_
#define _std_ext_algorithm_hpp_

#include <algorithm>

namespace std_ext {

//! a copy_if algo
//! see [Meyers, EffectiveSTL], Item 37 for more details
template<class InIt,
    class OutIt,
    class Pre>
OutIt copy_if(InIt begin,
              InIt end,
              OutIt destBegin,
              Pre p)
{
    while (begin != end)
    {
        if (p(*begin))  *destBegin++ = *begin;
        ++begin;
    }

    return destBegin;
}

//! a bubble sort algo (by Wledge/Trent/wraith)
template<class RanIt,
    class Fun>
void bubblesort(RanIt begin,
                RanIt end,
                Fun comp)
{
    bool swapped = false;
    --end;

    do
    {
        swapped = false;
        for (RanIt bubbleBegin = begin; bubbleBegin != end; ++bubbleBegin)
        {
            if (!comp(*bubbleBegin, *(bubbleBegin + 1)))
            {
                std::iter_swap(bubbleBegin, bubbleBegin + 1);
                swapped = true;
            }
        }
        --end;
    } while (swapped);
}

} // namespace std_ext

#endif // include guard
