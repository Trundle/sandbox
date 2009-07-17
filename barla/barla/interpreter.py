# -*- coding: utf-8 -*-

"""
    barla.interpreter
    ~~~~~~~~~~~~~~~~~

    A simple stack-based VM.
"""


from pypy.rlib.jit import JitDriver

from barla import opcodes
from barla.builtins import builtins
from barla.objects import Function


jitdriver = JitDriver(greens=['code', 'pc'], reds=['frame', 'consts',
                                                   'interpreter', 'stack'])


class Frame(object):
    def __init__(self, code, prev=None, jitted=False):
        self.code = code
        self.locals = {}
        self.next = None
        self.prev = prev
        self.jitted = jitted


class Interpreter(object):
    def __init__(self):
        self.frame = None
        self.stack = []

    def execute(self, code, with_jit=False):
        # Setup new frame
        self.frame, oldframe = Frame(code, self.frame, with_jit), self.frame
        if oldframe is not None:
            oldframe.next = self.frame
        # Prepare dispatch loop
        bytecode = code.code
        consts = code.consts
        pc = 0
        frame = self.frame
        stack = self.stack
        # The dispatch loop of barla's VM
        while pc < len(bytecode):
            if with_jit:
                jitdriver.jit_merge_point(code=bytecode, pc=pc,
                                          consts=consts, frame=frame,
                                          interpreter=self, stack=stack)
            stmt = bytecode[pc]
            pc += 1

            if stmt in [opcodes.ADD, opcodes.MUL, opcodes.SUB, opcodes.EQ,
                        opcodes.NE, opcodes.LT, opcodes.LE, opcodes.GT,
                        opcodes.GE]:
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
                elif stmt == opcodes.LT:
                    stack.append(lhs.lt(rhs))
                elif stmt == opcodes.LE:
                    stack.append(lhs.le(rhs))
                elif stmt == opcodes.GT:
                    stack.append(lhs.gt(rhs))
                elif stmt == opcodes.GE:
                    stack.append(lhs.ge(rhs))
            elif stmt == opcodes.JUMP_ABSOLUTE:
                target = ord(bytecode[pc])
                if with_jit and target < pc:
                    jitdriver.can_enter_jit(code=bytecode, pc=target,
                                            consts=consts, frame=frame,
                                            interpreter=self, stack=stack)
                pc = target
                continue
            elif stmt == opcodes.JUMP_IF_FALSE:
                if not stack.pop().true().boolvalue:
                    pc += ord(bytecode[pc])
                    continue
                pc += 1
            elif stmt == opcodes.JUMP_IF_TRUE:
                if stack.pop().true().boolvalue:
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
                # First, search the name in frame locals
                name = consts[index].str().strvalue
                try:
                    obj = frame.locals[name]
                except KeyError:
                    # Search in parent frames
                    pframe = frame.prev
                    while pframe is not None:
                        try:
                            obj = pframe.locals[name]
                        except KeyError:
                            pframe = pframe.prev
                        else:
                            break
                    else:
                        # Then search in builtins
                        obj = builtins[name]
                stack.append(obj)
            elif stmt == opcodes.STORE_NAME:
                index = ord(bytecode[pc])
                pc += 1
                frame.locals[consts[index].str().strvalue] = stack.pop()
            elif stmt == opcodes.CALL:
                func = stack.pop()
                n_args = ord(bytecode[pc])
                pc += 1
                args = [stack.pop() for _ in xrange(n_args)]
                stack.append(func.call(self, args))
            elif stmt == opcodes.RETURN:
                return stack.pop()
            elif stmt == opcodes.PRINT:
                print stack.pop().str().strvalue
            elif stmt == opcodes.MAKE_FUNCTION:
                index = ord(bytecode[pc])
                pc += 1
                code = consts[index]
                stack.append(Function(code))
            else:
                raise RuntimeError('Unknown opcode: ' + str(ord(stmt)))
