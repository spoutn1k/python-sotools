import logging
from functools import lru_cache
from sotools.dl_cache.flags import Flags
from sotools.dl_cache.dl_cache import _cache_libraries


@lru_cache()
def cache_libraries(cache_file: str = "/etc/ld.so.cache",
                    arch_flags: int = None):
    """
    Returns a dictionary with the contents of the given cache file
    (/etc/ld.so.cache by default)

    cache: path towards a linker cache file
    flags: flag value to look for. A null value will return binaries matching the interpreter,
        a non-null value will be used to filter out mismatching entries. See Flags.expected_flags

    Can be used to assume what libraries are installed on the system and where
    The keys are libraries' sonames; the values are the paths at which the
    corresponding shared object can be found
    """

    _arch_flags = arch_flags
    if _arch_flags is None:
        _arch_flags = Flags.expected_flags()

    with open(cache_file, 'rb') as cache_file:
        cache = cache_file.read()

    try:
        libs = _cache_libraries(cache)
    except Exception as err:
        logging.debug("DLCache parsing failed: %s", str(err))
        libs = []

    def _generate_values():
        for (soname, data) in libs:
            if data[0] == _arch_flags:
                yield (soname, data[1])

    return dict(_generate_values())


def host_libraries(cache_file="/etc/ld.so.cache"):
    return cache_libraries(cache_file)
