# -*- coding: utf-8 -*-

"""
    barla.interpreter
    ~~~~~~~~~~~~~~~~~

    A simple stack-based VM.
"""


from pypy.rlib.jit import JitDriver

from barla import opcodes


jitdriver = JitDriver(greens=['code', 'pc'], reds=['frame', 'consts', 'stack'])


class Frame(object):
    def __init__(self, code):
        self.code = code
        self.locals = {}


def execute(code, with_jit=False):
    frame = Frame(code)
    bytecode = code.code
    consts = code.consts
    pc = 0
    stack = []
    while pc < len(bytecode):
        if with_jit:
            jitdriver.jit_merge_point(code=bytecode, pc=pc,
                                      consts=consts, frame=frame, stack=stack)
        stmt = bytecode[pc]
        pc += 1

        if stmt in [opcodes.ADD, opcodes.MUL, opcodes.SUB, opcodes.EQ, opcodes.NE]:
            rhs = stack.pop()
            lhs = stack.pop()

            if stmt == opcodes.ADD:
                stack.append(lhs.add(rhs))
            elif stmt == opcodes.MUL:
                stack.append(lhs.mul(rhs))
            elif stmt == opcodes.SUB:
                stack.append(lhs.sub(rhs))
            elif stmt == opcodes.EQ:
                stack.append(lhs.eq(rhs))
            elif stmt == opcodes.NE:
                stack.append(lhs.ne(rhs))
        elif stmt == opcodes.JUMP_ABSOLUTE:
            target = ord(bytecode[pc])
            if with_jit and target < pc:
                jitdriver.can_enter_jit(code=bytecode, pc=target,
                                        consts=consts, frame=frame,
                                        stack=stack)
            pc = target
            continue
        elif stmt == opcodes.JUMP_IF_FALSE:
            if not stack.pop().true():
                pc += ord(bytecode[pc])
                continue
            pc += 1
        elif stmt == opcodes.JUMP_IF_TRUE:
            if stack.pop().true():
                pc += ord(bytecode[pc])
                continue
            pc += 1
        elif stmt == opcodes.LOAD_CONST:
            index = ord(bytecode[pc])
            pc += 1
            stack.append(consts[index])
        elif stmt == opcodes.LOAD_NAME:
            index = ord(bytecode[pc])
            pc += 1
            stack.append(frame.locals[consts[index].str()])
        elif stmt == opcodes.STORE_NAME:
            index = ord(bytecode[pc])
            pc += 1
            frame.locals[consts[index].str()] = stack.pop()
        elif stmt == opcodes.PRINT:
            print stack.pop().str()
        else:
            raise RuntimeError('Unknown opcode: ' + str(ord(stmt)))
