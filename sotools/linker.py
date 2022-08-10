"""
Implementation of the dynamic linker search algorithm
Rules in ld.so(8)
"""

import os
from typing import Optional, List
from functools import lru_cache
from pathlib import Path
from sotools.dl_cache import cache_libraries
from sotools.dl_cache.flags import Flags
import logging


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


def resolve(soname: str,
            rpath: Optional[str] = None,
            runpath: Optional[str] = None,
            arch_flags: Optional[Flags] = None) -> Optional[str]:
    """
    Get a path towards a library from a given soname.
    Implements system rules and takes the environment into account

    soname:     'key' to lookup for a library
    rpath:      rpath to use for this lookup
    runpath:    runpath to use for this lookup
    arch_flags: flags to look for; useful for 32bit libraries on 64bit systems
                See sotools.dl_cache.flags.Flags for info

    The method will return a resolved path for the given soname or None if
    no matching entry could be found.
    """

    found = Path()

    def _found() -> bool:
        """Check if a returned path corresponds to the soname"""
        return found != Path()

    def _valid(path: Path) -> bool:
        """Check a path is an existing directory"""
        return path.is_dir()

    def _search_paths(soname: str, paths: List[Path], reason: str) -> Path:
        """Search a list of paths and return the first match"""
        if paths:
            path_list_str = os.pathsep.join(map(lambda x: x.as_posix(), paths))
            logging.debug(f"search path={path_list_str}\t\t({reason or ''})")

        for dir_ in filter(_valid, paths):
            potential_lib = Path(dir_, soname)
            logging.debug(f"trying file={potential_lib.as_posix()}")
            if potential_lib.exists():
                return potential_lib

        return Path()

    rpath = list(map(Path, list(rpath or [])))
    ld_library_path = list(map(Path, _linker_path()[0]))
    runpath = list(map(Path, list(runpath or [])))
    cache_entries = cache_libraries(arch_flags=arch_flags)
    system_path = list(map(Path, _linker_path()[1]))

    logging.debug(f"find library={soname}; searching")

    dynamic_paths = [
        (rpath, 'RPATH'),
        (ld_library_path, 'LD_LIBRARY_PATH'),
        (runpath, 'RUNPATH'),
    ]

    default_paths = [(system_path, 'SYSTEM')]

    for tuple_ in dynamic_paths:
        if not _found():
            found = _search_paths(soname, *tuple_)

    if not _found():
        logging.debug("search cache=/etc/ld.so.cache")
        if soname in cache_entries:
            found = Path(cache_entries[soname])

    for tuple_ in default_paths:
        if not _found():
            found = _search_paths(soname, *tuple_)

    return found.resolve() if _found() else None
