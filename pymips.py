import sys
import assembler

def main():
    args = sys.argv[1:]
    assembler.assemble(args[0], args[1], args[2])

if __name__ == "__main__": main()
