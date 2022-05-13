#!/bin/env python3

import os
import sys

from sotools.dl_cache import _cache_libraries, Flags

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s <cache file>" % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    try:
        with open(sys.argv[1], 'rb') as cache_file:
            cache = cache_file.read()
    except Exception:
        sys.exit(1)

    libraries = _cache_libraries(cache)
    for library in libraries.items():
        print(
            f"\t{library[0]} ({Flags.description(library[1][0])}) => {library[1][1]}"
        )
    sys.exit(0)
