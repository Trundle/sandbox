# -*- coding: utf-8 -*-

import re
import sre_compile
import sre_parse
from pypy.rlib.rsre import rsre, rsre_char, rsre_core
from pypy.module.unicodedata import unicodedb_5_0_0 as unicodedb

from barla import opcodes
from barla.builtins import b_None
from barla.objects import Code, Int, Str

rsre.set_unicode_db(unicodedb)


# A small regex implementation

class RePattern(object):
    def __init__(self, pattern):
        self.code, self.groups = re_compile(pattern)

    def match(self, string):
        state = rsre.SimpleStringState(string)
        if state.match(self.code):
            return ReMatch(self, state)

class ReMatch(object):
    def __init__(self, pattern, state):
        self.pattern = pattern
        self.state = state
        self.regs = state.create_regs(pattern.groups)
        self.string = self.state.string

    def _get_slice(self, group, default):
        start, stop = self.regs[group]
        if start >= 0 and stop >= 0:
            return self.string[start:stop]
        else:
            return default

    def end(self, group=0):
        index = self.regs[group][1]
        assert index >= 0
        return index

    def group(self, group):
        return self._get_slice(group, None)

def re_compile(expr):
    """NOT_RPYTHON"""
    pattern = sre_parse.parse(expr)
    return (sre_compile._code(pattern, 0), pattern.pattern.groups)


# Parser framework

def parserize(parsers):
    """NOT_RPYTHON"""
    result = []
    for parser in parsers:
        if isinstance(parser, basestring):
            result.append(Word(re.escape(parser)))
        else:
            result.append(parser)
    return result


class ParseTreeNode(object):
    """
        Base class for all parse tree nodes.
    """
    def __init__(self):
        self.children = []

    def dump(self, indent=0):
        """
            Debug helper: dump the tree.
        """
        print ' ' * indent + str(self)
        for child in self.children:
            child.dump(indent + 4)

class WordNode(ParseTreeNode):
    def __init__(self, word):
        ParseTreeNode.__init__(self)
        self.word = word

    def dump(self, indent=0):
        print ' ' * indent + str(self), self.word

class Result(object):
    def __init__(self, tree, rest):
        self.tree = tree
        self.rest = rest

class Parser(object):
    """
        Base class for all parsers.
    """
    def __init__(self, transformer=None, *args, **kwargs):
        """NOT_RPYTHON"""
        super(Parser, self).__init__(*args, **kwargs)
        self.parser = None
        self.transformer = transformer

    def match(self, string):
        match = self.parser.match(string)
        if match is not None and self.transformer is not None:
            match.tree = self.transformer(match.tree)
        return match

class Word(Parser):
    def __init__(self, expr, *args, **kwargs):
        """NOT_RPYTHON"""
        super(Word, self).__init__(*args, **kwargs)
        expr = '\s*(%s)' % (expr, )
        self.regex = RePattern(expr)

    def match(self, string):
        match = self.regex.match(string)
        if match:
            return Result(WordNode(match.group(1)), string[match.end():])
        return None

class Any(Parser):
    def __init__(self, *parsers, **kwargs):
        """NOT_RPYTHON"""
        super(Any, self).__init__(**kwargs)
        self.parsers = parserize(parsers)

    def match(self, string):
        for parser in self.parsers:
            match = parser.match(string)
            if match is not None:
                return match
        return None

class Opt(Parser):
    """
        Optionally match a given parser. This parser never fails.
    """
    def __init__(self, parser, *args, **kwargs):
        """NOT_RPYTHON"""
        super(Opt, self).__init__(*args, **kwargs)
        self.parser = parser

    def match(self, string):
        match = self.parser.match(string)
        if match is not None:
            return match
        return Result(ASTNode(), string)

class Rep(Parser):
    """
        Match `parser` as often as possible. This parser never fails.
    """
    def __init__(self, parser, *args, **kwargs):
        """NOT_RPYTHON"""
        super(Rep, self).__init__(*args, **kwargs)
        self.parser = parser

    def match(self, string):
        result = ASTNode()
        while True:
            match = self.parser.match(string)
            if match is None:
                break
            string = match.rest
            result.children.append(match.tree)
        return Result(result, string)

class Seq(Parser):
    """
        Match a sequence of parsers.
    """
    def __init__(self, *parsers, **kwargs):
        """NOT_RPYTHON"""
        super(Seq, self).__init__(**kwargs)
        self.parsers = parserize(parsers)

    def match(self, string):
        result = ASTNode()
        for parser in self.parsers:
            match = parser.match(string)
            if match is None:
                return None
            string = match.rest
            result.children.append(match.tree)
        return Result(result, string)

def setup(dict_):
    """NOT_RPYTHON
        Initialises the parser framework.
    """
    parsers = [n for n in dict_.iterkeys() if n.startswith('p_')]
    # Create parser instances first, so other parsers can reference them
    for name in parsers:
        dict_[name[2:]] = Parser(dict_[name])
    # Now set the real parsers
    for name in parsers:
        dict_[name[2:]].parser = eval(dict_[name].__doc__, dict_, dict_)


# Parsers

def left(lhs, seq):
    if seq:
        return left(BinaryOp(seq[0].children[0].word, lhs, seq[0].children[1]),
                    seq[1:])
    else:
        return lhs

def p_expression(tree):
    "Seq(term, Rep(Seq(Any('+', '-', '*'), term)))"
    return left(tree.children[0], tree.children[1].children)

def p_term(tree):
    "Seq(Any(number, name, string), Rep(call))"
    term = tree.children[0]
    if tree.children[1].children:
        for arglist in tree.children[1].children:
            term = Call(term, arglist.children)
    return term

def p_call(tree):
    "Seq('(', Opt(arglist), ')')"
    return tree.children[1]

def p_arglist(tree):
    "Seq(Rep(Seq(expression, ',')), expression)"
    arguments = [child.children[0] for child in
                 tree.children[0].children]
    arguments.append(tree.children[1])
    tree = ASTNode()
    tree.children = arguments
    return tree

def p_name(tree):
    r"Word(r'\w+')"
    return Name(tree.word)

def p_number(tree):
    r"Word(r'[+-]?\d+')"
    assert tree.word is not None
    value = int(tree.word)
    return Const(Int(value))

def p_paramlist(tree):
    "Seq(Rep(Seq(name, ',')), name)"
    params = [child.children[0] for child in
                 tree.children[0].children]
    params.append(tree.children[1])
    tree = ASTNode()
    tree.children = params
    return tree

def p_string(tree):
    r"""Word(r"'[^\n]*?'")"""
    value = tree.word[1:]
    return Const(Str(value[:-1]))

def p_assign_stmt(tree):
    "Seq(name, ':=', expression)"
    return Assign(tree.children[0].name, tree.children[2])

def p_funcdef(tree):
    "Seq(name, '(', Opt(paramlist), ')', ':', statements, '.')"
    name = tree.children[0].name
    params = [child.name for child in tree.children[2].children]
    body = tree.children[5].children
    return FunctionDef(name, params, body)

def p_if_stmt(tree):
    "Seq('if', condition, ':', statements, '.')"
    return If(tree.children[1], tree.children[3].children)

def p_if_else_stmt(tree):
    "Seq('if', condition, ':', statements, '.', 'else', ':', statements, '.')"
    return IfElse(tree.children[1], tree.children[3].children,
                  tree.children[7].children)

def p_while_stmt(tree):
    "Seq('while', condition, ':', statements, '.')"
    return While(tree.children[1], tree.children[3].children)

def p_condition(tree):
    """Seq(expression, Rep(Seq(Any('==', '!=', '<=', '<', '>=', '>'),
                               expression)))"""
    return left(tree.children[0], tree.children[1].children)

def p_print_stmt(tree):
    "Seq('print', expression)"
    return Print(tree.children[1])

def p_return_stmt(tree):
    "Seq('return', expression)"
    return Return(tree.children[1])

def p_statements(tree):
    """Rep(Any(assign_stmt, funcdef, if_else_stmt, if_stmt, print_stmt,
               return_stmt, while_stmt))"""
    return tree


# Our AST

class ASTNode(ParseTreeNode):
    """
        Base class for all AST nodes.
    """

class Assign(ASTNode):
    def __init__(self, name, expr):
        ASTNode.__init__(self)
        self.name = name
        self.expr = expr

    def compile(self, code, consts, flags):
        flags = self.expr.compile(code, consts, flags)
        name = Str(self.name)
        try:
            index = consts.index(name)
        except ValueError:
            index = len(consts)
            consts.append(name)
        code.append(opcodes.STORE_NAME)
        code.append(chr(index))
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self), self.name
        self.expr.dump(indent + 4)

class BinaryOp(ASTNode):
    ops = {
        '+': opcodes.ADD,
        '-': opcodes.SUB,
        '*': opcodes.MUL,
        '==': opcodes.EQ,
        '!=': opcodes.NE,
        '<': opcodes.LT,
        '<=': opcodes.LE,
        '>': opcodes.GT,
        '>=': opcodes.GE
    }
    def __init__(self, op, left, right):
        ASTNode.__init__(self)
        self.op = op
        self.left = left
        self.right = right

    def compile(self, code, consts, flags):
        flags = self.left.compile(code, consts, flags)
        flags = self.right.compile(code, consts, flags)
        code.append(self.ops[self.op])
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self), self.op
        self.left.dump(indent + 4)
        self.right.dump(indent + 4)

class Call(ASTNode):
    def __init__(self, expr, arguments):
        self.expr = expr
        self.arguments = arguments

    def compile(self, code, consts, flags):
        arguments = list(self.arguments)
        arguments.reverse()
        for arg in arguments:
            flags = arg.compile(code, consts, flags)
        self.expr.compile(code, consts, flags)
        code.append(opcodes.CALL)
        code.append(chr(len(self.arguments)))
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self)
        self.expr.dump(indent + 4)
        for arg in self.arguments:
            arg.dump(indent + 4)

class Const(ASTNode):
    """
        AST node representing a constant value.
    """
    def __init__(self, value):
        ASTNode.__init__(self)
        self.constvalue = value

    def compile(self, code, consts, flags):
        try:
            index = consts.index(self.constvalue)
        except ValueError:
            index = len(consts)
            consts.append(self.constvalue)
        code.append(opcodes.LOAD_CONST)
        code.append(chr(index))
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self), self.constvalue.str().strvalue

class FunctionDef(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

    def compile(self, code, consts, flags):
        # Compile function code
        fcode = []
        fconsts = []
        fflags = 0
        params = list(self.params)
        params.reverse()
        # Pop parameters from stack to names in the new function
        for name in params:
            fcode.append(opcodes.STORE_NAME)
            fcode.append(chr(len(fconsts)))
            fconsts.append(Str(name))
        # Compile the new function's code
        for stmt in self.body:
            fflags = stmt.compile(fcode, fconsts, fflags)
        # Default return value
        fcode.append(opcodes.LOAD_CONST)
        fcode.append(chr(len(fconsts)))
        fconsts.append(b_None)
        fcode.append(opcodes.RETURN)
        # Add creation code
        codeobj = Code(''.join(fcode), fconsts, fflags)
        code.append(opcodes.MAKE_FUNCTION)
        code.append(chr(len(consts)))
        consts.append(codeobj)
        code.append(opcodes.STORE_NAME)
        code.append(chr(len(consts)))
        consts.append(Str(self.name))
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self) + '%s(%s)' % (self.name,
                                                     ', '.join(self.params))
        for stmt in self.body:
            stmt.dump(indent + 4)

class If(ASTNode):
    def __init__(self, condition, body):
        ASTNode.__init__(self)
        self.condition = condition
        self.body = body

    def compile(self, code, consts, flags):
        flags = self.condition.compile(code, consts, flags)
        code.append(opcodes.JUMP_IF_FALSE)
        jump_offset_pos = len(code)
        # Placeholder
        code.append(chr(0xff))

        for stmt in self.body:
            flags = stmt.compile(code, consts, flags)

        code[jump_offset_pos] = chr(len(code) - jump_offset_pos)
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self)
        self.condition.dump(indent + 4)
        for stmt in self.body:
            stmt.dump(indent + 4)

class IfElse(ASTNode):
    def __init__(self, condition, body, else_body):
        ASTNode.__init__(self)
        self.condition = condition
        self.body = body
        self.else_body = else_body

    def compile(self, code, consts, flags):
        flags = self.condition.compile(code, consts, flags)
        code.append(opcodes.JUMP_IF_FALSE)
        jump_offset_pos = len(code)
        # Placeholder
        code.append(chr(0xff))

        for stmt in self.body:
            flags = stmt.compile(code, consts, flags)
        code.append(opcodes.JUMP_ABSOLUTE)
        # Add jump flag
        flags |= 1
        end_if_jump_offset_pos = len(code)
        # Placeholder
        code.append(chr(0xff))

        code[jump_offset_pos] = chr(len(code) - jump_offset_pos)

        for stmt in self.else_body:
            flags = stmt.compile(code, consts, flags)

        code[end_if_jump_offset_pos] = chr(len(code))
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self)
        self.condition.dump(indent + 4)
        print ' ' * (indent + 1) + 'body:'
        for stmt in self.body:
            stmt.dump(indent + 8)
        print ' ' * (indent + 1) + 'else body:'
        for stmt in self.else_body:
            stmt.dump(indent + 8)


class Name(ASTNode):
    def __init__(self, name):
        ASTNode.__init__(self)
        self.name = name

    def compile(self, code, consts, flags):
        name = Str(self.name)
        try:
            index = consts.index(name)
        except ValueError:
            index = len(consts)
            consts.append(name)
        code.append(opcodes.LOAD_NAME)
        code.append(chr(index))
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self), self.name

class Print(ASTNode):
    def __init__(self, expr):
        ASTNode.__init__(self)
        self.expr = expr

    def compile(self, code, consts, flags):
        flags = self.expr.compile(code, consts, flags)
        code.append(opcodes.PRINT)
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self)
        self.expr.dump(indent + 4)

class Return(ASTNode):
    def __init__(self, expr):
        ASTNode.__init__(self)
        self.expr = expr

    def compile(self, code, consts, flags):
        flags = self.expr.compile(code, consts, flags)
        code.append(opcodes.RETURN)
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self)
        self.expr.dump(indent + 4)

class While(ASTNode):
    def __init__(self, condition, body):
        ASTNode.__init__(self)
        self.condition = condition
        self.body = body

    def compile(self, code, consts, flags):
        loop_begin_pos = len(code)
        flags = self.condition.compile(code, consts, flags)
        code.append(opcodes.JUMP_IF_FALSE)
        jump_offset_pos = len(code)
        # Placeholder
        code.append(chr(0xff))

        for stmt in self.body:
            flag = stmt.compile(code, consts, flags)
        code.append(opcodes.JUMP_ABSOLUTE)
        code.append(chr(loop_begin_pos))
        # Add jump flag
        flags |= 1

        code[jump_offset_pos] = chr(len(code) - jump_offset_pos)
        return flags

    def dump(self, indent=0):
        print ' ' * indent + str(self)
        self.condition.dump(indent + 4)
        for stmt in self.body:
            stmt.dump(indent + 4)


setup(globals())
