
#ifndef Std_extTriple_hpp_
#define Std_extTriple_hpp_

namespace std_ext
{

// a triple class
template<class First, 
    class Second,
    class Third> 
class triple
{
public:
    // some typedefs
    typedef triple<First, Second, Third> myT;
    typedef First firstT;
    typedef Second secondT;
    typedef Third thirdT;

    // data
    firstT first;
    secondT second;
    thirdT third;

    // constructors
    triple(const firstT& f = firstT(), const secondT& s = secondT(),
        const thirdT& t = thirdT()) : first(f), second(s), third(t) {}
    template<class F, class S, class T> 
    triple(const triple<F, S, T>& t) : first(t.first), second(t.second), third(t.third) {}

    // =-operator
    template<class F, class S, class T> 
    myT& operator=(const triple<F, S, T>& t) {
        this->first = t.first;
        this->second = t.second;
        this->third = t.third;

        return *this;
    }

    // swap two triples
    void swap(myT& rhs) {
        myT tmp(rhs);

        rhs = *this;
        *this = tmp;
    }
};

// create a triple
template<class F, class S, class T>
triple<F, S, T> makeTriple(const F& f, const S& s, const T& t) {
    return (triple<F, S, T>(f, s, t));
}

// swap twp triples
template<class F, class S, class T>
void swap(triple<F, S, T>& t1, triple<F, S, T>& t2) {
    t1.swap(t2);
}

// some operators

// ==-operator
template<class F1, class S1, class T1, class F2, class S2, class T2>
bool operator ==(const triple<F1, S1, T1>& t1, const triple<F2, S2, T2>& t2) {
    return ((t1.first == t2.first) && (t1.second == t2.second) && (t1.third == t2.third));
}

// !=-operator
template<class F1, class S1, class T1, class F2, class S2, class T2>
bool operator !=(const triple<F1, S1, T1>& t1, const triple<F2, S2, T2>& t2) {
    return !(t1 == t2);
}

// <-operator
template<class F1, class S1, class T1, class F2, class S2, class T2>
bool operator <(const triple<F1, S1, T1>& t1, const triple<F2, S2, T2>& t2) {
    return ((t1.first < t2.first) && (t1.second < t2.second) && (t1.third < t2.third));
}

// <=-operator
template<class F1, class S1, class T1, class F2, class S2, class T2>
bool operator <=(const triple<F1, S1, T1>& t1, const triple<F2, S2, T2>& t2) {
    return ((t1 < t2) || (t1 == t2));
}

// >-operator
template<class F1, class S1, class T1, class F2, class S2, class T2>
bool operator >(const triple<F1, S1, T1>& t1, const triple<F2, S2, T2>& t2) {
    return !(t1 <= t2);
}

// >=-operator
template<class F1, class S1, class T1, class F2, class S2, class T2>
bool operator >=(const triple<F1, S1, T1>& t1, const triple<F2, S2, T2>& t2) {
    return !(t1 < t2);
}

} // namespace std_ext

#endif // include guard
