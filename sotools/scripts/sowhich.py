#!/bin/env python3

import sys
import logging
from argparse import ArgumentParser
from sotools.linker import resolve

DESCRIPTION = """This program will attempt to resolve an ELF file from a given shared object name. It allows to trace the attempts made by the linker to determine what shared object is resolved by what means."""
EPILOG = """Please report any mismatch between the dynamic linker and the output of this program to http://github.com/spoutn1k/python-sotools."""

PARSER = ArgumentParser(
    prog='sowhich',
    description=DESCRIPTION,
    epilog=EPILOG,
)

PARSER.add_argument(
    "soname",
    help="The library name to search for.",
)

PARSER.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Trace resolving attempts while searching for the library",
)


def main():
    args = PARSER.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
        )

    path = resolve(args.soname)
    if path:
        print(path)
        sys.exit(0)
    sys.exit(1)
