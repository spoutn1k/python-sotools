"""
Implementation of the dynamic linker search algorithm
Rules in ld.so(8)
"""

import os
from typing import (
    List,
    Optional,
    Tuple,
)
from functools import lru_cache
from pathlib import Path
from sotools.dl_cache import cache_libraries
from sotools.dl_cache.flags import Flags
import logging

DEFAULT_PATHS = ['/lib', '/usr/lib', '/lib64', '/usr/lib64']


class LinkingError(Exception):
    pass


@lru_cache()
def _linker_path() -> Tuple[List[str], List[str]]:
    """
    Return linker search paths, in order
    Sourced from `man ld.so`
    """
    ld_library_path = list(
        filter(
            None,
            os.environ.get('LD_LIBRARY_PATH', "").split(':'),
        ))

    return (ld_library_path, DEFAULT_PATHS)


def _valid(path: Path) -> bool:
    """Check a path is an existing directory"""
    return path.is_dir()


def _search_paths(
    soname: str,
    paths: List[Path],
    reason: str = "",
) -> Optional[Path]:
    """
    Search a list of paths for a given soname and return the first match

    soname:     The library name to search
    paths:      The list of paths to look into
    reason:     To mimic LD_DEBUG, optional reason of the search
    """
    if paths:
        path_list_str = os.pathsep.join(map(lambda x: x.as_posix(), paths))
        logging.debug(f"search path={path_list_str}\t\t({reason or ''})")

    for dir_ in filter(_valid, paths):
        potential_lib = Path(dir_, soname)
        logging.debug(f"trying file={potential_lib.as_posix()}")
        if potential_lib.exists():
            return potential_lib

    return None


def resolve(
    soname: str,
    rpath: Optional[List[str]] = None,
    runpath: Optional[List[str]] = None,
    arch_flags: Optional[Flags] = None,
    absolute: bool = False,
) -> Optional[Path]:
    """
    Get a path towards a library from a given soname.
    Implements system rules and takes the environment into account

    soname:     'key' to lookup for a library
    rpath:      rpath to use for this lookup
    runpath:    runpath to use for this lookup
    arch_flags: flags to look for; useful for 32bit libraries on 64bit systems
                See sotools.dl_cache.flags.Flags for info
    absolute:   output an absolute path to the final object if a link is found

    The method will return a resolved path for the given soname or None if
    no matching entry could be found.
    """

    found = None

    def _found() -> bool:
        """Check if a returned path corresponds to the soname"""
        return found not in {None, Path()}

    rpath = list(map(Path, list(rpath or [])))
    runpath = list(map(Path, list(runpath or [])))
    cache_entries = cache_libraries(arch_flags=arch_flags)
    system_path = map(Path, _linker_path()[1])

    env_path, system_path = _linker_path()
    env_path = list(map(Path, env_path))
    system_path = list(map(Path, system_path))

    logging.debug(f"find library={soname}; searching")

    dynamic_paths = [
        (rpath, 'RPATH'),
        (env_path, 'LD_LIBRARY_PATH'),
        (runpath, 'RUNPATH'),
    ]

    # First, search the paths that are set by the user at run-time
    for paths, name in dynamic_paths:
        if not _found() and paths:
            found = _search_paths(soname, paths, name)

    # Query the cache for a match
    if not _found():
        logging.debug("search cache=/etc/ld.so.cache")
        if soname in cache_entries:
            found = Path(cache_entries[soname])

    default_paths = [(system_path, 'SYSTEM')]

    # Finally, search the hardcoded system paths
    for tuple_ in default_paths:
        if not _found():
            found = _search_paths(soname, *tuple_)

    if _found():
        logging.debug(f"found matching library={found}")
        if absolute:
            found = found.resolve()
            logging.debug(f"-> link to library={found}")
        return found

    return None
