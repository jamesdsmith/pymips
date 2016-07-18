import sys
from exceptions import *
from utils import SymbolTable, write_inst_hex

def inst_needs_relocation(instruction):
    return (instruction >> 26) == 2 or (instruction >> 26) == 3

def relocate_inst(instruction, offset, symtbl, reltbl):
    jump_addr = symtbl.get_addr(reltbl.get_label(offset))
    return (instruction & 0xfc000000) | (jump_addr >> 2)

def parse_table_entry(line):
    tokens = line.split("\t")
    return tokens[0], tokens[1]

def build_tables(obj_code, symtbl, reltbl):
    mode = None
    tables = [symtbl, reltbl]
    for line in obj_code:
        if line == ".symbol":
            # mode = "symbol"
            mode = 0
        elif line == ".relocation":
            # mode = "relocation"
            mode = 1
        elif line != "" and mode != None:
            # add this entry to the correct table
            addr, label = parse_table_entry(line)
            tables[mode].add(label, int(addr))

def find_text_block(obj_code):
    start = 0
    end = 0
    found_text = False
    index = 0
    for line in obj_code:
        if line == ".text":
            found_text = True
            start = index + 1
        elif found_text and line == "":
            end = index
            found_text = False
        index += 1
    return start, end

def link(input_file, out_file):
    # check args?
    obj_code = []
    with open(input_file, 'r') as f:
        for line in f:
            if len(line) > 0:
                obj_code += [line.strip()]
    # build symbol/relocation tables
    symtbl = SymbolTable(False)
    reltbl = SymbolTable(True)
    build_tables(obj_code, symtbl, reltbl)
    # Find .text section of input
    byte_off = 0
    output = []
    errors = []
    line_num = 0
    start, end = find_text_block(obj_code)
    for line in obj_code[start:end]:
        try:
            line_num += 1
            # write instruction out
            instruction = int(line, 16)
            if inst_needs_relocation(instruction):
                instruction = relocate_inst(instruction, byte_off, symtbl, reltbl)
            write_inst_hex(output, instruction)
        except AssemblerException as e:
            errors += [(line_num, e)]
        byte_off += 4

    if len(errors) > 0:
        print("Errors during linking:")
        for line_num, e in errors:
            print("Error: line {0}: {1}".format(line_num, e))

    with open(out_file, 'w') as f:
        for line in output:
            f.write(line + '\n')

def main():
    args = sys.argv[1:]
    link(args[0], args[1])

if __name__ == "__main__": main()
