# -*- coding: utf-8 -*-

"""
    barla.objects
    ~~~~~~~~~~~~~

    Barla's object model.
"""


from pypy.rlib.rarithmetic import ovfcheck


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
        return '<Object>'

    def true(self):
        return True


class Bool(Object):
    def __init__(self, value):
        self.boolvalue = value

    def true(self):
        return self.boolvalue


class Int(Object):
    def __init__(self, value):
        self.intvalue = value

    def eq(self, other):
        return Bool(self.intvalue == other.intvalue)

    def ne(self, other):
        return Bool(self.intvalue != other.intvalue)

    def add(self, other):
        return Int(ovfcheck(self.intvalue + other.intvalue))

    def mul(self, other):
        return Int(ovfcheck(self.intvalue * other.intvalue))

    def sub(self, other):
        return Int(ovfcheck(self.intvalue - other.intvalue))

    def str(self):
        return str(self.intvalue)

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
        return self.strvalue

    def true(self):
        return bool(self.strvalue)
