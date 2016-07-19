import sys
import argparse
import assembler
import linker
import os

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
        ints, outs = assembler.assemble(input_file)
        obj_code += [outs]
        if args.int:
            with open(os.path.splitext(input_file)[0] + ".int", 'w') as f:
                for line in ints:
                    f.write(line + '\n')
        if args.obj:
            with open(os.path.splitext(input_file)[0] + ".o", 'w') as f:
                for line in outs:
                    f.write(line + '\n')

    if args.link != None:
        for link_file in args.link:
            with open(link_file, 'r') as f:
                obj_code += [[]]
                for line in f:
                    obj_code[-1] += [line.strip()]
    output = linker.link(obj_code)
    with open(args.out_name, 'w') as f:
        for line in output:
            f.write(line + '\n')

if __name__ == "__main__": main()
