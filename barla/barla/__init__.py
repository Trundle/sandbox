# -*- encoding: utf-8 -*-

"""
    barla
    ~~~~~

    A small and senseless language.
"""

from pypy.rlib.streamio import open_file_as_stream

from barla.interpreter import Interpreter
from barla.objects import Code
from barla.parsing import RePattern, statements


class BarlaSyntaxError(Exception):
    pass


whitespaces = RePattern('\s*')
def compile(filename):
    f = open_file_as_stream(filename)
    source = f.readall()
    f.close()

    result = statements.match(source)
    # Remove trailing whitespaces
    match = whitespaces.match(result.rest)
    if match:
        result.rest = result.rest[match.end():]
    if result.rest:
        raise BarlaSyntaxError(result.rest)

    print 'Parse tree:'
    result.tree.dump()

    bytecode = []
    consts = []
    for stmt in result.tree.children:
        stmt.compile(bytecode, consts)

    return Code(''.join(bytecode), consts)
