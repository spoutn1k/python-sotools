#!/bin/env python3

import sys
import logging
from argparse import ArgumentParser
from sotools.ldd import ldd, NotELFError

DESCRIPTION = """List dynamic dependencies. This program will output a complete list of all the dynamic dependencies of the dynamic executable passed as an argument. This python version is safe to use on untrusted binaries."""
EPILOG = """Please report any mismatch between the dynamic linker and the output of this program to http://github.com/spoutn1k/python-sotools."""

PARSER = ArgumentParser(
    prog='ldd.py',
    description=DESCRIPTION,
    epilog=EPILOG,
)

PARSER.add_argument(
    "executable",
    help="Path to an executable to analyze.",
)

PARSER.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Trace resolving attempts while searching for the dependencies",
)


def main():
    args = PARSER.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
        )

    try:
        libs = ldd(args.executable)
    except NotELFError:
        print("\tnot a dynamic executable")
        sys.exit(1)

    print("\n".join(libs.ldd_format()))
    sys.exit(0)
