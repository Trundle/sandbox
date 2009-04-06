/*! \file binary_write.hpp
The binary_write lib ...
*/

#ifndef _std_ext_binary_write_hpp_
#define _std_ext_binary_write_hpp_

namespace std_ext
{

//! writes a binary value to a stream
/*! \param os the (output-)stream
    \param t value to write
    \return the given stream
*/
template<class T,
    class C,
    class CT>
std::basic_ostream<C, CT>& write_binary(std::basic_ostream<C, CT>& os, const T& t)
{
    os.write(reinterpret_cast<const C*>(&t), sizeof(T));
    return os;
}

//! reads a binary value from a stream
/*! \param is the (input-)stream
    \param t where the value should be stored
    \return the given stream
*/
template<class T,
    class C,
    class CT>
std::basic_istream<C, CT>& read_binary(std::basic_istream<C, CT>& is, T& t)
{
    is.read(reinterpret_cast<C*>(&t), sizeof(T));
    return is;
}

//! helper functor for operator <<
template<class T>
struct binary_writer
{
    typedef T type_to_write;
    const type_to_write to_write_;

    binary_writer(const type_to_write& t)
        : to_write_(t) {}
};

//! helper functor for operator >>
template<class T>
struct binary_reader
{
    typedef T type_to_read;
    type_to_read& to_read_;

    binary_reader(type_to_read& t)
        : to_read_(t) {}
};

//! 
template<class T>
binary_writer<T> write_binary(const T& t)
{
    return binary_writer<T>(t);
}

template<class T>
binary_reader<T> read_binary(T& t)
{
    return binary_reader<T>(t);
}

//! 
template<class T,
    class C,
    class CT>
std::basic_ostream<C, CT>& operator <<(std::basic_ostream<C, CT>& os, const binary_writer<T>& bw)
{
    return write_binary(os, bw.to_write_);
}

//!
template<class T,
    class C,
    class CT>
std::basic_istream<C, CT>& operator >>(std::basic_istream<C, CT>& is, binary_reader<T>& br)
{
    return read_binary(is, br.to_read_);
}

}

} // namespace std_ext

#endif // include guard
