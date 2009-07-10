# -*- coding: utf-8 -*-


import time
from pypy.jit.backend.hlinfo import highleveljitinfo
from pypy.jit.metainterp.policy import JitPolicy

from barla import compile, execute


def entry_point(args):
    """
        Main entry point of the stand-alone executable:
        takes a list of strings and returns the exit code.
    """
    # Store args[0] in a place where the JIT log can find it (used by
    # viewcode.py to know the executable whose symbols it should display)
    highleveljitinfo.sys_executable = args[0]

    if len(args) < 2:
        print 'Usage: %s <filename> [--jit]' % (args[0], )
        return 1

    code = compile(args[1])

    start = time.clock()
    execute(code, False)
    stop = time.clock()
    print 'Non jitted: %f seconds' % (stop - start, )

    start = time.clock()
    execute(code, True)
    stop = time.clock()
    print 'Warmup jitted: %f seconds' % (stop - start, )

    start = time.clock()
    execute(code, True)
    stop = time.clock()
    print 'Warmed jitted: %f seconds' % (stop - start, )

    return 0


# ____________________________________________________________

def target(driver, args):
    return entry_point, None

def jitpolicy(driver):
    return JitPolicy()


if __name__ == '__main__':
    import sys
    entry_point(sys.argv)
