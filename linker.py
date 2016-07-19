import sys
import argparse
from exceptions import *
from utils import SymbolTable, write_inst_hex
import utils

def inst_needs_relocation(instruction):
    return (instruction >> 26) == 2 or (instruction >> 26) == 3

def relocate_inst(instruction, offset, symtbl, reltbl):
    jump_addr = symtbl.get_addr(reltbl.get_label(offset))
    return (instruction & 0xfc000000) | (jump_addr >> 2)

def parse_table_entry(line):
    tokens = line.split("\t")
    return tokens[0], tokens[1]

def build_tables(obj_code, symtbl, reltbls):
    mode = None
    tables = []
    for table in reltbls:
        tables += [(symtbl, table)]
    global_offset = 0
    index = 0
    for obj_file in obj_code:
        for line in obj_file:
            if line == ".symbol":
                # mode = "symbol"
                mode = 0
            elif line == ".relocation":
                # mode = "relocation"
                mode = 1
            elif line != "" and mode != None:
                # add this entry to the correct table
                addr, label = parse_table_entry(line)
                addr = int(addr)
                if mode == 0:
                    addr += global_offset
                tables[index][mode].add(label, addr)
        start, end = find_text_block(obj_file)
        global_offset += (end - start) * 4
        mode = None
        index += 1

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

def link(obj_code):
    # build symbol/relocation tables
    symtbl = SymbolTable(False)
    reltbls = []
    for i in range(0, len(obj_code)):
        reltbls += [SymbolTable(True)]
    build_tables(obj_code, symtbl, reltbls)
    # print(symtbl.to_string())
    # Find .text section of input
    byte_off = 0
    line_num = 0
    output = []
    errors = []
    index = 0
    for obj_file in obj_code:
        start, end = find_text_block(obj_file)
        for line in obj_file[start:end]:
            try:
                line_num += 1
                # write instruction out
                instruction = int(line, 16)
                if inst_needs_relocation(instruction):
                    instruction = relocate_inst(instruction, byte_off, symtbl, reltbls[index])
                write_inst_hex(output, instruction)
            except AssemblerException as e:
                errors += [(line_num, e)]
            byte_off += 4
        index += 1
        byte_off = 0
    if len(errors) > 0:
        print("Errors during linking:")
        for line_num, e in errors:
            print("Error: line {0}: {1}".format(line_num, e))
    return output

def main():
    parser = argparse.ArgumentParser(prog="linker", description='Link a MIPS program from multiple object files.')
    parser.add_argument("files", action="store", nargs="+", type=str, help="list of object files to process")
    parser.add_argument("-o", action="store", dest="out_name", type=str, default="mips.out", help="override output file name", metavar="file_name")
    args = parser.parse_args()

    obj_code = []
    for link_file in args.files:
        obj_code.append([x.strip() for x in utils.read_file_to_list(link_file)])
    output = link(obj_code)
    utils.write_file_from_list(args.out_name, output)

if __name__ == "__main__": main()
