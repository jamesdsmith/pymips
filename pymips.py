import sys
import assembler
import linker

def main():
    args = sys.argv[1:]
    assembler.assemble(args[0], args[1], args[2])
    linker.link(args[2], args[2] + "t")

if __name__ == "__main__": main()
