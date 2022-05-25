import logging
from typing import List
from dataclasses import dataclass
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

    libs.reverse()

    def _generate_values():
        for entry in libs:
            if entry.flags == _arch_flags:
                yield (entry.key, entry.value)

    return dict(_generate_values())


def host_libraries(cache_file="/etc/ld.so.cache"):
    return cache_libraries(cache_file)


def get_generator(data):
    header = _CacheHeader.deserialize(data)
    data = data[header.offset:]

    if not header.extension_offset:
        logging.info("Failed to retrieve generator: no extensions in cache")
        return ""

    extensions = cache_extension_sections(data[header.extension_offset:])

    for section in extensions:
        if section.tag == CacheExtensionTag.TAG_GENERATOR:
            return GeneratorSection(section).string_value(data)
    return ""
