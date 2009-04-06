
#ifndef _getter_setter_gs_hpp_
#define _getter_setter_gs_hpp_

#include "policies.hpp"

namespace gs
{

template<class T,
    template<class> class P = policies::default_policy>
class getter_setter
{
public:
    typedef getter_setter<T, P> my_type;
    typedef P<T> policy_type;
    typedef typename policy_type::value_type value_type;
    typedef typename policy_type::read_return_type read_return_type;
    typedef typename policy_type::write_return_type write_return_type;
    typedef typename policy_type::write_argument_type write_argument_type;
    typedef typename policy_type::constructor_argument_type constructor_argument_type;
private:
    value_type value_;
public:
    getter_setter() 
        : value_(policy_type::on_construct()) {}
    explicit getter_setter(constructor_argument_type val) 
        : value_(policy_type::on_construct(val)) {}
    getter_setter(const my_type& val)
        : value_(policy_type::on_copy_construct(val.value_)) {}

    my_type& operator=(const my_type& val)
    {
        (*this)(val.value_);
        return *this;
    }

    read_return_type operator()() const
    { 
        return policy_type::on_read(value_); 
    }

    write_return_type operator()(write_argument_type val)
    {
        return policy_type::on_write(value_, val);
    }
};

template<class T1,
    template<class> class P1,
    class T2,
    template<class> class P2>
bool operator==(const getter_setter<T1, P1>& lhs, const getter_setter<T2, P2>& rhs)
{
    return lhs() == rhs();
}

template<class T1,
    template<class> class P1,
    class T2,
    template<class> class P2>
bool operator!=(const getter_setter<T1, P1>& lhs, const getter_setter<T2, P2>& rhs)
{
    return lhs() != rhs();
}

template<class T1,
    template<class> class P1,
    class T2,
    template<class> class P2>
bool operator<(const getter_setter<T1, P1>& lhs, const getter_setter<T2, P2>& rhs)
{
    return lhs() < rhs();
}

template<class T1,
    template<class> class P1,
    class T2,
    template<class> class P2>
bool operator>(const getter_setter<T1, P1>& lhs, const getter_setter<T2, P2>& rhs)
{
    return lhs() > rhs();
}

template<class T1,
    template<class> class P1,
    class T2,
    template<class> class P2>
bool operator<=(const getter_setter<T1, P1>& lhs, const getter_setter<T2, P2>& rhs)
{
    return lhs() <= rhs();
}

template<class T1,
    template<class> class P1,
    class T2,
    template<class> class P2>
bool operator>=(const getter_setter<T1, P1>& lhs, const getter_setter<T2, P2>& rhs)
{
    return lhs() >= rhs();
}

}

#endif
