#!/bin/env python3

import os
import sys
import logging

from sotools.ldd import ldd, NotELFError

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s <ELF file>" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    if "--print-tries" in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        
    try:
        libs = ldd(sys.argv[1])
    except NotELFError:
        print("\tnot a dynamic executable")
        sys.exit(1)

    print("\n".join(libs.ldd_format()))
    sys.exit(0)
