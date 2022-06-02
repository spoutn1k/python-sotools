import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from functools import lru_cache
from sotools.dl_cache.flags import Flags
from sotools.dl_cache.dl_cache import (_CacheHeader, _FileEntryNew)
from sotools.dl_cache.structure import (BinaryStruct,
                                        deserialize_null_terminated_string)
from sotools.dl_cache.extensions.hwcaps import (HWCAPSection,
                                                dl_cache_hwcap_extension)
from sotools.dl_cache.extensions.generator import GeneratorSection
from sotools.dl_cache.extensions import (cache_extension_sections,
                                         CacheExtensionTag)


def get_generator(data: bytes) -> Optional[str]:
    """
    Return the generator string from cache data, if the cache is recent enough
    to posess extensions
    """
    header = _CacheHeader.deserialize(data)
    data = data[header.offset:]

    if not header.extension_offset:
        logging.debug("Failed to retrieve generator: no extensions in cache")
        return None

    extensions = cache_extension_sections(data[header.extension_offset:])

    for section in extensions:
        if section.tag == CacheExtensionTag.TAG_GENERATOR:
            return GeneratorSection(section).string_value(data)
    return None


@dataclass(frozen=True)
class ResolvedEntry:
    key: str
    value: str
    flags: int
    hwcaps: str = ""


def _cache_libraries(data: bytes) -> List[ResolvedEntry]:
    """
    Return a list of ResolvedEntry objects with all references resolved
    """
    header = _CacheHeader.deserialize(data)
    data = data[header.offset:]
    extensions = []

    if header.extension_offset:
        extensions = cache_extension_sections(data[header.extension_offset:])

    def resolve_hwcap_values():
        for extension in extensions:
            if extension.tag == CacheExtensionTag.TAG_GLIBC_HWCAPS:
                yield HWCAPSection(extension).string_value(data)

    hwcap_string_values = list(resolve_hwcap_values())

    def _entries(data: bytes) -> list:
        """
        Generate a list of FileEntryXXX from the type defined in the header
        """
        header_size = BinaryStruct.sizeof(header.__class__)
        entry_type = header.__class__.entry_type
        entry_size = BinaryStruct.sizeof(entry_type)

        for index in range(header.nlibs):
            offset = header_size + index * entry_size
            entry = entry_type.deserialize(data[offset:offset + entry_size])
            yield entry

    def _lookup(entry):
        """
        Translate string references to strings
        """
        lookup = deserialize_null_terminated_string
        hwcap_entry_string = ""

        if isinstance(entry,
                      _FileEntryNew) and dl_cache_hwcap_extension(entry):
            index = entry.hwcap & ((1 << 32) - 1)
            if index < len(hwcap_string_values):
                hwcap_entry_string = hwcap_string_values[index]

        fields = dict(key=lookup(data[entry.key:]),
                      value=lookup(data[entry.value:]),
                      flags=entry.flags,
                      hwcaps=hwcap_entry_string)

        return ResolvedEntry(**fields)

    return list(map(_lookup, _entries(data)))


@dataclass(frozen=True)
class DynamicLinkerCache:
    file: str
    generator: Optional[str] = None
    entries: List[ResolvedEntry] = field(default_factory=list)


@lru_cache()
def _parse_cache(
        cache_file: str = "/etc/ld.so.cache") -> Optional[DynamicLinkerCache]:
    try:
        with open(cache_file, 'rb') as cache_file:
            cache_data = cache_file.read()
    except OSError as err:
        logging.error("Failed to open rtld cache: %s", str(err))
        return None

    try:
        entries = _cache_libraries(cache_data)
    except Exception as err:
        logging.error("rtdl cache parsing failed: %s", str(err))
        return None

    generator = get_generator(cache_data)

    fields = dict(file=cache_file, entries=entries, generator=generator)

    return DynamicLinkerCache(**fields)


def cache_libraries(cache_file: str = "/etc/ld.so.cache",
                    arch_flags: Optional[int] = None) -> Dict[str, str]:
    """
    Returns a dictionary with a curated list of the given cache file contents
    (/etc/ld.so.cache by default)

    cache: path towards a linker cache file
    flags: flag value to look for. A null value will return binaries matching
        the interpreter, a non-null value will be used to filter out mismatching
        entries. See Flags.expected_flags to create flag values

    Can be used to assume what libraries are installed on the system and where
    The keys are libraries' sonames; the values are the paths at which the
    corresponding shared object can be found

    The cache files may contain multiple entries for the same soname that differ
    in their flags, OS ABI and hardware capabilities. The dict returned
    contains one entry per soname, the most likely to be picked on the current
    system.

    See _cache_libraries for finer-grain control over the cache's contents
    """

    _arch_flags = arch_flags
    if _arch_flags is None:
        _arch_flags = Flags.expected_flags()

    cache = _parse_cache(cache_file)

    libs = cache.entries
    libs.reverse()

    def _generate_values():
        for entry in libs:
            if entry.flags == _arch_flags:
                yield (entry.key, entry.value)

    return dict(_generate_values())


def search_cache(soname: str,
                 cache_file: str = "/etc/ld.so.cache",
                 arch_flags: Optional[int] = None) -> Optional[str]:
    """
    Returns the best match for the given soname in the given cache matching
    the given flags

    soname: soname to match against the cache
    cache:  path towards a linker cache file
    flags:  flag value to look for. A null value will return binaries matching
        the interpreter, a non-null value will be used to filter out mismatching
        entries. See Flags.expected_flags to create flag values
    """

    _arch_flags = arch_flags
    if _arch_flags is None:
        _arch_flags = Flags.expected_flags()

    cache = _parse_cache(cache_file)

    for entry in cache.entries:
        # TODO hwcaps check, OS ABI check
        if entry.key == soname and entry.flags == _arch_flags:
            return entry.value

    return None
