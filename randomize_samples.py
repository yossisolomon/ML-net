import argparse
from random import randint, seed
import os

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",required=True, help="The input file")
    parser.add_argument("-o", "--output",required=True, help="The output file")
    args = parser.parse_args()
    return args


def seed_rng():
    seed(os.urandom(16))


def main():
    args = parse_arguments()

    new_lines = []
    with open(args.input,"r") as f:
        for line in f:
            new_line = str(randint(0,1)) + line[1:]
            new_lines.append(new_line)

    with open(args.output,"w") as f:
        f.write("".join(new_lines))


if __name__ == '__main__':
    main()
