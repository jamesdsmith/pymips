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

RS = 0x0001
RT = 0x0002
RD = 0x0004
SHAMT = 0x0008
IMM = 0x0010
BRANCH_LABEL = 0x0020
JUMP_LABEL = 0x0040

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

def expected_args(code):
    count = 0
    while code > 0:
        if code & 1:
            count += 1
        code = code >> 1
    return count

def write_inst(output, opcode, args, addr, symtbl, reltbl, params, is_funct, imm_min, imm_max):
    if len(args) != len(params):
        raise incorrect_number_of_parameters(name_from_opcode(opcode), len(args), len(params))
    inst = 0x00000000
    if is_funct:
        inst = inst | opcode
    else:
        inst = inst | (opcode << 26)
    while len(params) > 0:
        param, params = params[0], params[1:]
        arg, args = args[0], args[1:]
        if param == RS:
            inst = inst | (translate_reg(arg) << 21)
        elif param == RT:
            inst = inst | (translate_reg(arg) << 16)
        elif param == RD:
            inst = inst | (translate_reg(arg) << 11)
        elif param == SHAMT:
            inst = inst | (translate_num(arg, 0, 31) << 6)
        elif param == IMM:
            inst = inst | (translate_num(arg, imm_min, imm_max) & 0xFFFF)
        elif param == BRANCH_LABEL:
            label_addr = symtbl.get_addr(arg)
            if not can_branch_to(addr, label_addr):
                raise branch_out_of_range()
            offset = (label_addr - addr - 4) >> 2
            inst = inst | (offset & 0xFFFF)
        elif param == JUMP_LABEL:
            reltbl.add(arg, addr)
    write_inst_hex(output, inst)

def can_branch_to(src_addr, dest_addr):
    diff = dest_addr - src_addr
    return (diff >= 0 and diff <= TWO_POW_SEVENTEEN) or (diff < 0 and diff >= -(TWO_POW_SEVENTEEN - 4))

jtype = {
    "j":       (0x02, [JUMP_LABEL]),
    "jal":     (0x03, [JUMP_LABEL]),
}

itype = {
    "beq":     (0x04, [RS, RT, BRANCH_LABEL], 0, 0),
    "bne":     (0x05, [RS, RT, BRANCH_LABEL], 0, 0),
    "blez":    (0x06, [RS, BRANCH_LABEL], 0, 0),
    "bgtz":    (0x07, [RS, BRANCH_LABEL], 0, 0),
    "addi":    (0x08, [RT, RS, IMM], INT16_MIN, INT16_MAX),
    "addiu":   (0x09, [RT, RS, IMM], INT16_MIN, INT16_MAX),
    "slti":    (0x0a, [RT, RS, IMM], INT16_MIN, INT16_MAX),
    "sltiu":   (0x0b, [RT, RS, IMM], 0, UINT16_MAX),
    "andi":    (0x0c, [RT, RS, IMM], 0, UINT16_MAX),
    "ori":     (0x0d, [RT, RS, IMM], 0, UINT16_MAX),
    "xori":    (0x0e, [RT, RS, IMM], 0, UINT16_MAX),
    "lui":     (0x0f, [RT, IMM], 0, UINT16_MAX),
    "lb":      (0x20, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "lh":      (0x21, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "lw":      (0x23, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "lbu":     (0x24, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "lhu":     (0x25, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "sb":      (0x28, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "sh":      (0x29, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "sw":      (0x2b, [RT, IMM, RS], INT16_MIN, INT16_MAX),
    "cache":   (0x2f),
    "ll":      (0x30),
    "lwc1":    (0x31),
    "lwc2":    (0x32),
    "pref":    (0x33),
    "ldc1":    (0x35),
    "ldc2":    (0x36),
    "sc":      (0x38),
    "swc1":    (0x39),
    "swc2":    (0x3a),
    "sdc1":    (0x3d),
    "sdc2":    (0x3e),
}

rtype = {
    "sll":     (0x00, [RD, RT, SHAMT]),
    "srl":     (0x02, [RD, RT, SHAMT]),
    "sra":     (0x03, [RD, RT, SHAMT]),
    "sllv":    (0x04, [RD, RT, RS]),
    "srlv":    (0x06, [RD, RT, RS]),
    "srav":    (0x07, [RD, RT, RS]),
    "jr":      (0x08, [RS]),
    "jalr":    (0x09, [RS]),
    "movz":    (0x0a, [RD, RS, RT]),
    "movn":    (0x0b, [RD, RS, RT]),
    "syscall": (0x0c, []),
    "break":   (0x0d, []),
    "sync":    (0x0f, []),
    "mfhi":    (0x10, [RD]),
    "mthi":    (0x11, [RS]),
    "mflo":    (0x12, [RD]),
    "mtlo":    (0x13, [RS]),
    "mult":    (0x18, [RS, RT]),
    "multu":   (0x19, [RS, RT]),
    "div":     (0x1a, [RS, RT]),
    "divu":    (0x1b, [RS, RT]),
    "add":     (0x20, [RD, RS, RT]),
    "addu":    (0x21, [RD, RS, RT]),
    "sub":     (0x22, [RD, RS, RT]),
    "subu":    (0x23, [RD, RS, RT]),
    "and":     (0x24, [RD, RS, RT]),
    "or":      (0x25, [RD, RS, RT]),
    "xor":     (0x26, [RD, RS, RT]),
    "nor":     (0x27, [RD, RS, RT]),
    "slt":     (0x2a, [RD, RS, RT]),
    "sltu":    (0x2b, [RD, RS, RT]),
    "tge":     (0x30, [RS, RT]),
    "tgeu":    (0x31, [RS, RT]),
    "tlt":     (0x32, [RS, RT]),
    "tltu":    (0x33, [RS, RT]),
    "teq":     (0x34, [RS, RT]),
    "tne":     (0x36, [RS, RT]),
}

translate_table = {}
translate_table.update(rtype)
translate_table.update(itype)
translate_table.update(jtype)

def name_from_opcode(opcode):
    for key in translate_table:
        if translate_table[key][1] == opcode:
            return key
    return ""

def translate_inst(output, name, args, addr, symtbl, reltbl):
    if name in translate_table:
        entry = translate_table[name]
        opcode = entry[0]
        params = entry[1]
        if name in itype:
            _, _, imm_min, imm_max = itype[name]
        imm = IMM in params
        write_inst(output, opcode, args, addr, symtbl, reltbl, params, name in rtype, imm_min if imm else 0, imm_max if imm else 0)
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
