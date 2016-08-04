import argparse
import re
from exceptions import *
from utils import SymbolTable, write_inst_hex
import utils

TWO_POW_SEVENTEEN = 131072
UINT16_MAX = 2**16 - 1
INT16_MAX = 2**15 - 1
INT16_MIN = -(2**15)
LONG_MAX = 2**63 - 1
LONG_MIN = -(2**63)

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
    """Translate a string representing a register into the number for that register

    >>> translate_reg("$zero")
    0

    >>> translate_reg("$s0")
    16
    """
    if register in register_table:
        return register_table[register]
    else:
        raise invalid_register_name(register)

def translate_num(number, lower_bound, upper_bound):
    """Translate a string containing a decimal or hex number into a number
    also makes sure that the number is within the supplied bounds
    Returns the translated number, and an integer error code

    >>> translate_num("1", 0, 10)
    1

    >>> translate_num("0x1", 0, 10)
    1

    >>> translate_num("0xABCD", LONG_MIN, LONG_MAX)
    43981
    """
    try:
        value = int(number, 0)
        if value < lower_bound or value > upper_bound:
            raise translate_num_out_of_range(value, lower_bound, upper_bound)
        else:
            return value
    except:
        raise translate_num_error(number)

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
    elif name == "blt":
        pass
    elif name == "bgt":
        pass
    elif name == "ble":
        pass
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

def write_bitwise_imm(output, opcode, args, addr, symtbl, reltbl):
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

def write_branch_on(output, opcode, args, addr, symtbl, reltbl):
    if len(args) != 2:
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), 2)
    rs = translate_reg(args[0])
    label_addr = symtbl.get_addr(args[1])
    if not can_branch_to(addr, label_addr):
        raise branch_out_of_range()
    offset = (label_addr - addr - 4) >> 2
    instruction = (opcode << 26) | (rs << 21) | (offset & 0xFFFF)
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

def not_yet_impl(*args):
    raise function_not_implemented()

translate_table = {
    "j":    (write_jump, 0x02),
    "jal":  (write_jump, 0x03),
    "beq":  (write_branch, 0x04),
    "bne":  (write_branch, 0x05),
    "blez": (write_branch_on, 0x06),
    "bgtz": (write_branch_on, 0x07),
    "addi": (write_addiu, 0x08),
    "addiu": (write_addiu, 0x09),
    "slti": (not_yet_impl, 0x0a),
    "sltiu": (not_yet_impl, 0x0b),
    "andi": (write_bitwise_imm, 0x0c),
    "ori":  (write_bitwise_imm, 0x0d),
    "xori": (write_bitwise_imm, 0x0e),
    "lui":  (write_lui, 0x0f),
    "lb":   (write_mem, 0x20),
    "lh":   (not_yet_impl, 0x21),
    "lwl":  (not_yet_impl, 0x22),
    "lw":   (write_mem, 0x23),
    "lbu":  (write_mem, 0x24),
    "lhu":  (not_yet_impl, 0x25),
    "lwr":  (not_yet_impl, 0x26),
    "sb":   (write_mem, 0x28),
    "sh":   (not_yet_impl, 0x29),
    "swl":  (not_yet_impl, 0x2a),
    "sw":   (write_mem, 0x2b),
    "swr":  (not_yet_impl, 0x2e),
    "cache": (not_yet_impl, 0x2f),
    "ll":   (not_yet_impl, 0x30),
    "lwc1": (not_yet_impl, 0x31),
    "lwc2": (not_yet_impl, 0x32),
    "pref": (not_yet_impl, 0x33),
    "ldc1": (not_yet_impl, 0x35),
    "ldc2": (not_yet_impl, 0x36),
    "sc":   (not_yet_impl, 0x38),
    "swc1": (not_yet_impl, 0x39),
    "swc2": (not_yet_impl, 0x3a),
    "sdc1": (not_yet_impl, 0x3d),
    "sdc2": (not_yet_impl, 0x3e),
    "sll":  (write_shift, 0x00),
    "srl":  (write_shift, 0x02),
    "sra":  (write_shift, 0x03),
    "sllv": (write_rtype, 0x04),
    "srlv": (write_rtype, 0x06),
    "srav": (write_rtype, 0x07),
    "jr":   (write_jr, 0x08),
    "jalr": (write_jr, 0x09),
    "movz": (not_yet_impl, 0x0a),
    "movn": (not_yet_impl, 0x0b),
    "syscall": (not_yet_impl, 0x0c),
    "break": (not_yet_impl, 0x0d),
    "sync": (not_yet_impl, 0x0f),
    "mfhi": (write_move, 0x10),
    "mthi": (not_yet_impl, 0x11),
    "mflo": (write_move, 0x12),
    "mtlo": (not_yet_impl, 0x13),
    "mult": (write_arith, 0x18),
    "multu": (not_yet_impl, 0x19),
    "div":  (write_arith, 0x1a),
    "divu": (not_yet_impl, 0x1b),
    "add":  (not_yet_impl, 0x20),
    "addu": (write_rtype, 0x21),
    "sub":  (not_yet_impl, 0x22),
    "subu": (not_yet_impl, 0x23),
    "and":  (not_yet_impl, 0x24),
    "or":   (write_rtype, 0x25),
    "xor":  (not_yet_impl, 0x26),
    "nor":  (not_yet_impl, 0x27),
    "slt":  (write_rtype, 0x2a),
    "sltu": (write_rtype, 0x2b),
    "tge":  (not_yet_impl, 0x30),
    "tgeu": (not_yet_impl, 0x31),
    "tlt":  (not_yet_impl, 0x32),
    "tltu": (not_yet_impl, 0x33),
    "teq":  (not_yet_impl, 0x34),
    "tne":  (not_yet_impl, 0x36),
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

def assemble(input_file):
    cleaned = [strip_comments(line).strip() for line in utils.read_file_to_list(input_file)]
    asm = [line for line in cleaned if line != ""]
    symtbl = SymbolTable(False)
    reltbl = SymbolTable(True)
    # Pass One
    intermediate, errors_one = pass_one(asm, symtbl)
    # Pass Two
    output, errors_two = pass_two(intermediate, symtbl, reltbl)

    if len(errors_one) > 0:
        print("Errors during pass one:")
        for line_num, e in errors_one:
            print("Error: line {0}: {1}".format(line_num, e))
    if len(errors_two) > 0:
        print("Errors during pass two:")
        for line_num, e in errors_two:
            print("Error: line {0}: {1}".format(line_num, e))
    if len(errors_one) > 0 or len(errors_two) > 0:
        print("One or more errors encountered during assembly operation")
    return intermediate, output

def main():
    parser = argparse.ArgumentParser(prog="mipsa", description='Assemble a MIPS assembly program. Outputs an object file for every input file.')
    parser.add_argument("files", action="store", nargs="+", type=str, help="list of assembly files to process")
    parser.add_argument("--int", action="store_true", default=False, help="output intermediate files")
    args = parser.parse_args()

    for input_file in args.files:
        ints, objs = assemble(input_file)
        file_name = utils.get_file_name(input_file)
        if args.int:
            int_file = file_name + ".int"
            utils.write_file_from_list(int_file, ints)
        obj_file = file_name + ".o"
        utils.write_file_from_list(obj_file, objs)

if __name__ == "__main__": main()
