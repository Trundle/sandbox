
#ifndef _std_ext_map_
#define _std_ext_map_

#include <functional>

namespace std_ext {

// map_add_update
//
// perform effictive adding and updating on a map (see [Meyers, EffectiveSTL], Item 24)
template<class _M,
    class _K,
    class _V>
typename _M::iterator map_add_update(_M& m,
                                     const _K& k,
                                     const _V& v)
{
    typename _M::iterator it = m.lower_bound(k);

    if (it != m.end() && !(m.key_comp()(k, it->first)))
    {
        it->second = v;
        return it;
    }
    else
        return m.insert(it, typename _M::value_type(k, v));
}

// find_map_entry_value
//
// find a map entry by value
template<class _M>
struct find_map_entry_value 
    : std::unary_function<const typename _M::value_type&, bool>
{
    typedef typename _M::mapped_type value_t;
    typedef const typename _M::value_type& argument_type;

    find_map_entry_value(const value_t& val) : m_value(val) {}

    bool operator()(argument_type p) const
    { 
        return (p.second == this->m_value);
    }

private:
    const value_t m_value;
};

// map_value_deleter
//
// deletes the value
template<class _M>
struct map_value_deleter
    : std::unary_function<typename _M::value_type&, void>
{
    typedef typename _M::value_type& argument_type;

    void operator()(argument_type p) const
    {
        delete p.second;
        p.second = 0;
    }
};  

} // namespace std_ext

#endif // include guard
