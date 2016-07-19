import sys
import argparse
import assembler
import linker
import os
import utils

def main():
    parser = argparse.ArgumentParser(prog="pymips", description='Assemble and link a MIPS assembly program.')
    parser.add_argument("files", action="store", nargs="+", type=str, help="list of assembly files to process")
    parser.add_argument("--int", action="store_true", default=False, help="output intermediate files")
    parser.add_argument("--obj", action="store_true", default=False, help="output object files")
    parser.add_argument("-o", action="store", dest="out_name", type=str, default="mips.out", help="override output file name", metavar="file_name")
    parser.add_argument("-l", "--link", action="append", help="add file to program when linking. This option can be used more than once", metavar="file_name")
    args = parser.parse_args()

    obj_code = []
    for input_file in args.files:
        ints, objs = assembler.assemble(input_file)
        obj_code.append(objs)
        # Might want to change this to remove the path and just get the file name itself
        file_name = os.path.splitext(input_file)[0]
        if args.int:
            int_file = file_name + ".int"
            utils.write_file_from_list(int_file, ints)
        if args.obj:
            obj_file = file_name + ".o"
            utils.write_file_from_list(obj_file, objs)
    if args.link != None:
        for link_file in args.link:
            obj_code.append([x.strip() for x in utils.read_file_to_list(link_file)])
    output = linker.link(obj_code)
    utils.write_file_from_list(args.out_name, output)

if __name__ == "__main__": main()
