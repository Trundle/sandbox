

opcodes = dict()
for (i, name) in enumerate('LOAD_CONST LOAD_NAME STORE_NAME ADD MUL SUB '
                           'EQ NE JUMP_ABSOLUTE JUMP_IF_FALSE '
                            'JUMP_IF_TRUE PRINT CALL'.split()):
    globals()[name] = chr(i)
    opcodes[chr(i)] = name
