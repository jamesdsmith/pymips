import sys
import string
import random
import re
import argparse
from exceptions import *

TWO_POW_SEVENTEEN = 131072
UINT16_MAX = 2**16 - 1
INT16_MAX = 2**15 - 1
INT16_MIN = -(2**15)
LONG_MAX = 2**63 - 1
LONG_MIN = -(2**63)

class SymbolTable:
    def __init__(self, allow_dupes):
        self.allow_dupes = allow_dupes
        self.table = {}

    def add(self, name, addr):
        if self.allow_dupes:
            if name not in self.table.keys():
                self.table[name] = []
            self.table[name] += [addr]
            return 0
        else:
            if name in self.table.keys():
                raise duplicate_label_found(name)
            else:
                self.table[name] = [addr]
                return 0

    def get_addr(self, name):
        if name not in self.table.keys():
            raise label_not_found(name)
        if len(self.table[name]) > 1:
            raise multiple_label_definitions(name)
        return self.table[name][0]

    def to_string(self):
        pairs = []
        for k in self.table:
            for v in self.table[k]:
                pairs += [(k, v)]
        output = []
        for k, v in sorted(pairs, key=lambda x: x[1]):
            output += [str(v) + "\t" + k]
        return output

def strip_comments(line):
    """Removes all text after a # the passed in string

    >>> strip_comments("Test string")
    'Test string'

    >>> strip_comments("Test #comment")
    'Test '

    >>> strip_comments("#hashtag")
    ''

    >>> strip_comments("Test#comment")
    'Test'
    """
    if "#" in line:
        return line[:line.find("#")]
    else:
        return line

def tokenize(line):
    """Split up a line of text on spaces, new lines, tabs, commas, parens
    returns the first word and the rest of the words
    
    >>> tokenize("This,Test")
    ('This', ['Test'])

    >>> tokenize("word1 word2 word3")
    ('word1', ['word2', 'word3'])

    >>> tokenize("word1, word2, word3")
    ('word1', ['word2', 'word3'])
    """
    tokens = [x for x in re.split("[ \f\n\r\t\v,()]+", line) if x]
    return tokens[0], tokens[1:]

def is_label(token):
    """Returns True if this token has a : at the end

    >>> is_label("label:")
    True

    >>> is_label("label")
    False

    >>> is_label(":::::")
    True
    """
    return token[-1] == ":"

def raise_inst_error(line_num, name, args):
    print("Error on line {0}: {1}".format(line_num, name + " " + " ".join(args)))

register_table = {
    "$zero": 0,
    "$0": 0,
    "$at": 1,
    "$v0": 2,
    "$v1": 3,
    "$a0": 4,
    "$a1": 5,
    "$a2": 6,
    "$a3": 7,
    "$t0": 8,
    "$t1": 9,
    "$t2": 10,
    "$t3": 11,
    "$t4": 12,
    "$t5": 13,
    "$t6": 14,
    "$t7": 15,
    "$s0": 16,
    "$s1": 17,
    "$s2": 18,
    "$s3": 19,
    "$s4": 20,
    "$s5": 21,
    "$s6": 22,
    "$s7": 23,
    "$t8": 24,
    "$t9": 25,
    "$k0": 26,
    "$k1": 27,
    "$gp": 28,
    "$sp": 29,
    "$fp": 30,
    "$ra": 31,
}

def translate_reg(register):
    if register in register_table:
        return register_table[register]
    else:
        raise invalid_register_name(register)

def translate_num(number, lower_bound, upper_bound):
    """Translate a string containing a decimal or hex number into a number
    also makes sure that the number is within the supplied bounds
    Returns the translated number, and an integer error code

    >>> translate_num("1", 0, 10)
    (1, 0)

    >>> translate_num("10", 0, 1)
    (0, -1)

    >>> translate_num("0x1", 0, 10)
    (1, 0)

    >>> translate_num("0xABCD", LONG_MIN, LONG_MAX)
    (43981, 0)
    """
    try:
        value = int(number, 0)
        if value < lower_bound or value > upper_bound:
            raise translate_num_out_of_range(value, lower_bound, upper_bound)
        else:
            return value
    except:
        raise translate_num_error(number)

def write_inst_hex(output, instruction):
    output += ["{:08x}".format(instruction)]

def write_pass_one(name, args):
    if name == "li":
        if len(args) != 2:
            raise incorrect_number_of_parameters(name, len(args), 2)
        imm = translate_num(args[1], LONG_MIN, LONG_MAX)
        if imm <= 0xffff and imm >= -0xffff:
            return ["addiu {0} $0 {1}".format(args[0], imm)]
        else:
            return ["lui $at {0}".format((imm >> 16) & 0xffff),
                    "ori {0} $at {1}".format(args[0], imm & 0xffff)]
    elif name == "move":
        if len(args) != 2:
            raise incorrect_number_of_parameters(name, len(args), 2)
        return ["addu {0} {1} $0".format(args[0], args[1])]
    elif name == "rem":
        if len(args) != 3:
            raise incorrect_number_of_parameters(name, len(args), 3)
        return ["div {0} {1}".format(args[1], args[2]),
                "mfhi {0}".format(args[0])]
    elif name == "bge":
        if len(args) != 3:
            raise incorrect_number_of_parameters(name, len(args), 3)
        return ["slt $at {0} {1}".format(args[0], args[1]),
                "beq $at $0 {0}".format(args[2])]
    elif name == "bnez":
        if len(args) != 2:
            raise incorrect_number_of_parameters(name, len(args), 2)
        return ["bne {0} $0 {1}".format(args[0], args[1])]
    else:
        return ["{0} {1}".format(name, " ".join(args))]

def write_rtype(output, funct, args, addr, symtbl, reltbl):
    if len(args) != 3:
        raise incorrect_number_of_parameters(name_from_opcode(funct), len(args), 3)
    rd = translate_reg(args[0])
    rs = translate_reg(args[1])
    rt = translate_reg(args[2])
    instruction = (rs << 21) | (rt << 16) | (rd << 11) | funct;
    write_inst_hex(output, instruction)

def write_shift(output, funct, args, addr, symtbl, reltbl):
    if len(args) != 3:
        raise incorrect_number_of_parameters(name_from_opcode(funct), len(args), 3)
    rd = translate_reg(args[0])
    rt = translate_reg(args[1])
    shamt = translate_num(args[2], 0, 31)
    instruction = (rt << 16) | (rd << 11) | (shamt << 6) | funct;
    write_inst_hex(output, instruction)

def write_jr(output, funct, args, addr, symtbl, reltbl):
    if len(args) != 1:
        raise incorrect_number_of_parameters(name_from_opcode(funct), len(args), 1)
    rs = translate_reg(args[0])
    instruction = (rs << 21) | funct
    write_inst_hex(output, instruction)

def write_addiu(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 3:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 3)
    rt = translate_reg(args[0]);
    rs = translate_reg(args[1]);
    imm = translate_num(args[2], INT16_MIN, INT16_MAX);
    instruction = (opcode << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
    write_inst_hex(output, instruction)

def write_ori(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 3:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 3)
    rt = translate_reg(args[0])
    rs = translate_reg(args[1])
    imm = translate_num(args[2], 0, UINT16_MAX)
    instruction = (opcode << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
    write_inst_hex(output, instruction)

def write_lui(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 2:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 2)
    rt = translate_reg(args[0])
    imm = translate_num(args[1], 0, UINT16_MAX)
    instruction = (opcode << 26) | (rt << 16) | (imm & 0xFFFF)
    write_inst_hex(output, instruction)

def write_mem(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 3:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 3)
    rt = translate_reg(args[0])
    rs = translate_reg(args[2])
    imm = translate_num(args[1], INT16_MIN, INT16_MAX)
    instruction = (opcode << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
    write_inst_hex(output, instruction)

def can_branch_to(src_addr, dest_addr):
    diff = dest_addr - src_addr
    return (diff >= 0 and diff <= TWO_POW_SEVENTEEN) or (diff < 0 and diff >= -(TWO_POW_SEVENTEEN - 4))

def write_branch(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 3:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 3)
    rs = translate_reg(args[0])
    rt = translate_reg(args[1])
    label_addr = symtbl.get_addr(args[2])
    if not can_branch_to(addr, label_addr):
        raise branch_out_of_range()
    offset = (label_addr - addr - 4) >> 2
    instruction = (opcode << 26) | (rs << 21) | (rt << 16) | (offset & 0xFFFF)
    write_inst_hex(output, instruction)

def write_jump(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 1:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 1)
    reltbl.add(args[0], addr)
    instruction = (opcode << 26)
    write_inst_hex(output, instruction)

def write_arith(output, funct, args, addr, symtbl, reltbl):
    if len(args) != 2:
        raise incorrect_number_of_parameters(name_from_opcode(funct), len(args), 2)
    rs = translate_reg(args[0])
    rt = translate_reg(args[1])
    instruction = (rs << 21) | (rt << 16) | funct
    write_inst_hex(output, instruction)

def write_move(output, funct, args, addr, symtbl, reltbl):
    if len(args) != 1:
        raise incorrect_number_of_parameters(name_from_opcode(funct), len(args), 2)
    rd = translate_reg(args[0])
    instruction = (rd << 11) | funct
    write_inst_hex(output, instruction)

translate_table = {
    "addu": (write_rtype, 0x21),
    "or": (write_rtype, 0x25),
    "slt": (write_rtype, 0x2a),
    "sltu": (write_rtype, 0x2b),
    "sll": (write_shift, 0x00),
    "jr": (write_jr, 0x08),
    "addiu": (write_addiu, 0x09),
    "ori": (write_ori, 0x0d),
    "lui": (write_lui, 0x0f),
    "lb": (write_mem, 0x20),
    "lbu": (write_mem, 0x24),
    "lw": (write_mem, 0x23),
    "sb": (write_mem, 0x28),
    "sw": (write_mem, 0x2b),
    "beq": (write_branch, 0x04),
    "bne": (write_branch, 0x05),
    "j": (write_jump, 0x02),
    "jal": (write_jump, 0x03),
    "mult": (write_arith, 0x18),
    "div": (write_arith, 0x1a),
    "mfhi": (write_move, 0x10),
    "mflo": (write_move, 0x12),
}

def name_from_opcode(opcode):
    for key in translate_table:
        if translate_table[key][1] == opcode:
            return key
    return ""

def translate_inst(output, name, args, addr, symtbl, reltbl):
    if name in translate_table:
        translate_func, funct = translate_table[name]
        translate_func(output, funct, args, addr, symtbl, reltbl)
    else:
        raise translate_inst_error(name, args)

def pass_one(lines, symtbl):
    errors = []
    ret_code = 0
    line_num = 0
    byte_off = 0
    intermediate = []
    for line in lines:
        try:
            line_num += 1
            name, args = tokenize(line)
            if name == "":
                continue
            if is_label(name):
                err = symtbl.add(name[:-1], byte_off)
                if len(args) == 0:
                    continue
                name = args[0]
                args = args[1:]
            instructions = write_pass_one(name, args)
            intermediate += instructions
            byte_off += len(instructions) * 4
        except AssemblerException as e:
            errors += [(line_num, e)]
            ret_code = -1
    return intermediate, errors

def pass_two(lines, symtbl, reltbl):
    output = [".text"]
    errors = []
    line_num = 0
    byte_off = 0
    for line in lines:
        try:
            line_num += 1
            name, args = tokenize(line)
            translate_inst(output, name, args, byte_off, symtbl, reltbl)
            byte_off += 4
        except AssemblerException as e:
            errors += [(line_num, e)]
    output += ["", ".symbol"] + symtbl.to_string()
    output += ["", ".relocation"] + reltbl.to_string()
    return output, errors

def assemble(input_file, int_file, out_file):
    asm = []
    with open(input_file, 'r') as f:
        for line in f:
            clean = strip_comments(line).strip()
            if len(clean) > 0:
                asm += [clean.strip()]
    symtbl = SymbolTable(False)
    reltbl = SymbolTable(True)
    # Pass One
    intermediate, errors_one = pass_one(asm, symtbl)
    with open(int_file, 'w') as f:
        for line in intermediate:
            f.write(line + '\n')
    # Pass Two
    output, errors_two = pass_two(intermediate, symtbl, reltbl)

    errors = errors_one + errors_two
    if len(errors) > 0:
        for line_num, e in sorted(errors, key=lambda x: x[0]):
            print("Error: line {0}: {1}".format(line_num, e))
        print("One or more errors encountered during assembly operation")

    with open(out_file, 'w') as f:
        for line in output:
            f.write(line + '\n')


def main():
    args = sys.argv[1:]
    assemble(args[0], args[1], args[2])

if __name__ == "__main__": main()
