#!/bin/env python3

import sys

from sotools.linker import resolve

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s <libmpi.so.x>" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    if path := resolve(sys.argv[1]):
        print(path)
        sys.exit(0)
    sys.exit(1)
