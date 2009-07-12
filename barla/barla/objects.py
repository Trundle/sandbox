# -*- coding: utf-8 -*-

"""
    barla.objects
    ~~~~~~~~~~~~~

    Barla's object model.
"""


from pypy.rlib.rarithmetic import ovfcheck
from pypy.rlib.rbigint import rbigint


class Object(object):
    """
        Base class for all objects.
    """
    def eq(self, other):
        return Bool(self == other)

    def ne(self, other):
        return Bool(self != other)

    def add(self, other):
        raise TypeError()

    def mul(self, other):
        raise TypeError()

    def sub(self, other):
        raise TypeError()

    def call(self):
        raise TypeError()

    def str(self):
        return Str('<Object>')

    def int(self):
        raise TypeError()

    def long(self):
        return Long(intvalue=self.int().intvalue)

    def true(self):
        return True


class Bool(Object):
    def __init__(self, value):
        self.boolvalue = value

    def true(self):
        return self.boolvalue


class Long(Object):
    def __init__(self, intvalue=0, longvalue=None):
        if longvalue is not None:
            self.longvalue = longvalue
        else:
            self.longvalue = rbigint.fromint(intvalue)

    def add(self, other):
        return Long(longvalue=self.longvalue.add(other.long().longvalue))

    def mul(self, other):
        return Long(longvalue=self.longvalue.mul(other.long().longvalue))

    def sub(self, other):
        return Long(longvalue=self.longvalue.sub(other.long().longvalue))

    def int(self):
        raise OverflowError()

    def long(self):
        return self

    def str(self):
        return Str(self.longvalue.str())

    def true(self):
        return self.longvalue.tobool()


def to_long_on_overflow(method):
    long_method = getattr(Long, method.__name__)

    def wrapper(self, other):
        try:
            return method(self, other)
        except OverflowError:
            return long_method(self.long(), other)
    return wrapper


class Int(Object):
    def __init__(self, value):
        self.intvalue = value

    def eq(self, other):
        return Bool(self.intvalue == other.intvalue)

    def ne(self, other):
        return Bool(self.intvalue != other.intvalue)

    @to_long_on_overflow
    def add(self, other):
        return Int(ovfcheck(self.intvalue + other.int().intvalue))

    @to_long_on_overflow
    def mul(self, other):
        return Int(ovfcheck(self.intvalue * other.int().intvalue))

    @to_long_on_overflow
    def sub(self, other):
        return Int(ovfcheck(self.intvalue - other.int().intvalue))

    def str(self):
        return Str(str(self.intvalue))

    def int(self):
        return self

    def long(self):
        return Long(intvalue=self.intvalue)

    def true(self):
        return bool(self.intvalue)


class Str(Object):
    def __init__(self, value):
        self.strvalue = value

    def add(self, other):
        if not isinstance(other, Str):
            raise TypeError()
        return Str(self.strvalue + other.strvalue)

    def mul(self, other):
        if not isinstance(other, Int):
            raise TypeError()
        string = [self.strvalue for _ in xrange(other.intvalue)]
        return Str(''.join(string))

    def str(self):
        return self

    def true(self):
        return bool(self.strvalue)
