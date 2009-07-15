# -*- coding: utf-8 -*-

"""
    barla.builtin
    ~~~~~~~~~~~~~

    Builtin functions of barla.
"""

from barla.objects import BuiltinFunction, Int, None_


builtins = {}


@BuiltinFunction
def b_str(args):
    if len(args) > 1:
        raise TypeError('too much arguments')
    return args[0].str()
builtins['str'] = b_str


b_None = None_()
builtins['None'] = b_None
