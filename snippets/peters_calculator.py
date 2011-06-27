# encoding: utf-8
# Solution to "Peter's Calculator".
#
# Implements its own simple parser framework. A parser is simply a
# callable taking the input string as argument. It either returns a
# pair (match, remaining string) or a false-y value if the parser
# didn't match.
#
# Copyright (c) 2011 Andreas Stührk

from __future__ import with_statement
import contextlib
import re
import operator
import sys

def regex_parser(pattern):
    "Matches the given regex pattern."
    def parser(data):
        match = pattern.match(data)
        if match:
            return (match.group(1), data[match.end():])
        return None

    pattern = re.compile(r"\s*(%s)" % (pattern, ))
    return parser

# Convenient shortcut
r = regex_parser

def any(*parsers):
    """Matches any of the given parsers. The first matching parser will
    win. Fails if no parser matches."""
    def parser(data):
        for parser in parsers:
            match = parser(data)
            if match:
                return match
        return None
    return parser

def seq(*parsers):
    "Matches a sequence of parsers."
    def parser(data):
        result = list()
        for parser in parsers:
            match = parser(data)
            if match:
                (match, data) = match
                result.append(match)
            else:
                return None
        return (result, data)
    return parser

def repeat(parser):
    "Match `parser` as often as possible. This parser never fails."
    def wrapped(data):
        result = list()
        while True:
            match = parser(data)
            if match:
                (match, data) = match
                result.append(match)
            else:
                break
        return (result, data)
    return wrapped

class ForwardParser(object):
    "A parser that will be defined later."

    def __init__(self):
        self.parser = None

    def __call__(self, data):
        if self.parser is None:
            raise RuntimeError("undefined forward parser")
        return self.parser(data)

    def define(self, parser):
        "Returns `parser` so it can be used as decorator."
        if self.parser is not None:
            raise RuntimeError("forward parser already defined")
        self.parser = parser
        return parser

def rule(parser):
    def decorator(func):
        def matcher(data):
            match = parser(data)
            if match:
                (match, data) = match
                return (func(match), data)
            return None
        return matcher
    return decorator

# Parsers

p_expr = ForwardParser()

@rule(r("-?[0-9]+"))
def p_number(number):
    return NumberNode(int(number))

@rule(r("[a-zA-Z][a-zA-Z0-9]*"))
def p_var(name):
    return VarNode(name)

@rule(any(seq(r("\\("), p_expr, r("\\)")), seq(p_var), seq(p_number)))
def p_factor(ast):
    if ast[0] == "(":
        return ast[1]
    else:
        return ast[0]

@rule(seq(p_factor, repeat(seq(r("\\*"), p_factor))))
def p_term(ast):
    left = ast[0]
    for (op, right) in ast[1]:
        left = BinOpNode(left, op, right)
    return left

@p_expr.define
@rule(seq(p_term, repeat(seq(r("[+-]"), p_term))))
def p_expr(ast):
    left = ast[0]
    for (op, right) in ast[1]:
        left = BinOpNode(left, op, right)
    return left

@rule(seq(p_var, r(":="), p_expr))
def p_assign(ast):
    return AssignNode(ast[0], ast[2])

@rule(seq(r("PRINT"), p_var))
def p_print(ast):
    return PrintNode(ast[1])

@rule(r("RESET"))
def p_reset(ast):
    return ResetNode()

@rule(seq(any(p_assign, p_print, p_reset), r("\n")))
def p_line(ast):
    return ast[0]

@rule(seq(p_line, repeat(p_line)))
def p_lines(ast):
    return [ast[0]] + ast[1]

# Abstract Syntax Tree

UNDEFINED = "UNDEF"

class AssignNode(object):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def evaluate(self, state):
        state.namespace[self.var.name] = self.expr

class BinOpNode(object):
    OPERATORS = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul
    }
    def __init__(self, left, op, right):
        self.left = left
        self.right = right
        self.op = op

    def evaluate(self, state):
        left = self.left.evaluate(state)
        right = self.right.evaluate(state)
        if left == UNDEFINED or right == UNDEFINED:
            return UNDEFINED
        return self.OPERATORS[self.op](left, right)

class NumberNode(object):
    def __init__(self, value):
        self.value = value

    def evaluate(self, state):
        return self.value

class PrintNode(object):
    def __init__(self, var):
        self.var = var

    def evaluate(self, state):
        print self.var.evaluate(state)

class ResetNode(object):
    def evaluate(self, state):
        state.namespace.clear()

class VarNode(object):
    def __init__(self, name):
        self.name = name

    def evaluate(self, state):
        value = state.namespace.get(self.name, UNDEFINED)
        if value != UNDEFINED:
            try:
                with state.detect_cycle(self):
                    value = value.evaluate(state)
            except CycleDetected:
                value = UNDEFINED
        return value

class CycleDetected(Exception):
    "Raised when a variable references to itself."

class State(object):
    "Saves the calculator's state."

    def __init__(self):
        self.namespace = dict()
        self.evaluating = set()

    @contextlib.contextmanager
    def detect_cycle(self, var):
        """Helper context manager for detecting self-referencing
        variable definitions. Raises `CycleDetected` if a cycle is
        detected."""
        if var.name in self.evaluating:
            raise CycleDetected
        self.evaluating.add(var.name)
        try:
            yield
        finally:
            self.evaluating.remove(var.name)

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if args:
        with open(args[0], "r") as source_file:
            source = source_file.read()
    else:
        source = sys.stdin.read()
    result = p_lines(source)
    if result:
        (ast, data) = result
        state = State()
        for line in ast:
            line.evaluate(state)
    else:
        sys.stderr.write("Invalid input.\n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
