# -*- coding: utf-8 -*-

"""
    barla.objects
    ~~~~~~~~~~~~~

    Barla's object model.
"""

from pypy.rlib.rarithmetic import ovfcheck
from pypy.rlib.rbigint import rbigint


def generic_on(exc_type):
    """NOT_RPYTHON"""
    def decorator(method):
        generic_method = getattr(Object, method.__name__)

        def wrapper(self, other):
            try:
                return method(self, other)
            except exc_type:
                return generic_method(self.long(), other)
        return wrapper
    return decorator


class Object(object):
    """
        Base class for all objects.
    """
    def eq(self, other):
        return Bool(self == other)

    def ne(self, other):
        return Bool(self != other)

    def le(self, other):
        return Bool(not self.gt(other).boolvalue)

    def lt(self, other):
        return Bool(self.eq(other).boolvalue or self.le(other).boolvalue)

    def ge(self, other):
        return Bool(self.eq(other).boolvalue or not self.lt(other).boolvalue)

    def gt(self, other):
        return Bool(not(self.eq(other).boolvalue or self.lt(other).boolvalue))

    def add(self, other):
        raise TypeError()

    def mul(self, other):
        raise TypeError()

    def sub(self, other):
        raise TypeError()

    def call(self, interpreter, args):
        raise TypeError('not callable')

    def str(self):
        return Str('<Object>')

    def int(self):
        raise TypeError()

    def long(self):
        return Long(intvalue=self.int().intvalue)

    def true(self):
        return Bool(True)


class Bool(Object):
    def __init__(self, value):
        self.boolvalue = value

    def str(self):
        return Str(str(self.boolvalue))

    def true(self):
        return self


class BuiltinFunction(Object):
    def __init__(self, func):
        self.func = func

    def call(self, interpreter, args):
        return self.func(args)


class Function(Object):
    def __init__(self, code):
        self.func_code = code

    def call(self, interpreter, args):
        interpreter.stack.extend(args)
        return interpreter.execute(self.func_code)

    def str(self):
        return Str('<Function>')

class Long(Object):
    def __init__(self, intvalue=0, longvalue=None):
        if longvalue is not None:
            self.longvalue = longvalue
        else:
            self.longvalue = rbigint.fromint(intvalue)

    @generic_on(TypeError)
    def eq(self, other):
        return Bool(self.longvalue == other.long().longvalue)

    @generic_on(TypeError)
    def ne(self, other):
        return Bool(self.longvalue != other.long().longvalue)

    def ge(self, other):
        return self.lt(other)

    def lt(self, other):
        return Bool(self.longvalue.lt(other.long().longvalue))

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
        return Bool(self.longvalue.tobool())


def to_long_on_overflow(method):
    """NOT_RPYTHON"""
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

    @generic_on(TypeError)
    def eq(self, other):
        return Bool(self.intvalue == other.int().intvalue)

    @generic_on(TypeError)
    def ne(self, other):
        return Bool(self.intvalue != other.int().intvalue)

    def lt(self, other):
        return Bool(self.intvalue < other.int().intvalue)

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
        return Bool(bool(self.intvalue))


class None_(Object):
    def str(self):
        return Str('None')

    def true(self):
        return Bool(False)


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
        return Bool(bool(self.strvalue))


# Internal objects

class Code(Object):
    def __init__(self, code, consts):
        self.code = code
        self.consts = consts
