"""
Implementation of the dynamic linker search algorithm
Rules in ld.so(8)
"""

import os
from functools import lru_cache
from pathlib import Path
from sotools.dl_cache import host_libraries


class LinkingError(Exception):
    pass


@lru_cache()
def _linker_path():
    """
    Return linker search paths, in order
    Sourced from `man ld.so`
    """
    default_path = ['/lib', '/usr/lib', '/lib64', '/usr/lib64']
    ld_library_path = os.environ.get('LD_LIBRARY_PATH', "").split(':')

    return (ld_library_path, default_path)


def resolve(soname, rpath=None, runpath=None):
    """
    Get a path towards a library from a given soname.
    Implements system rules and takes the environment into account
    """

    found = None
    rpath = rpath or []
    runpath = runpath or []

    def _valid(path):
        return os.path.exists(path) and os.path.isdir(path)

    dynamic_paths = list(rpath) + _linker_path()[0] + list(runpath)
    default_paths = _linker_path()[1]

    for dir_ in filter(_valid, dynamic_paths):
        potential_lib = Path(dir_, soname).as_posix()
        if os.path.exists(potential_lib):
            found = potential_lib

    if not found and soname in host_libraries().keys():
        found = host_libraries()[soname]

    if not found:
        for dir_ in filter(_valid, default_paths):
            potential_lib = Path(dir_, soname).as_posix()
            if os.path.exists(potential_lib):
                found = potential_lib

    return os.path.realpath(found) if found else None
