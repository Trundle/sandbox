

opcodes = dict()
for (i, name) in enumerate('LOAD_CONST LOAD_NAME STORE_NAME ADD MUL SUB '
                           'EQ NE LT LE GT GE JUMP_ABSOLUTE JUMP_IF_FALSE '
                           'JUMP_IF_TRUE PRINT CALL MAKE_FUNCTION '
                           'RETURN'.split()):
    globals()[name] = chr(i)
    opcodes[chr(i)] = name
