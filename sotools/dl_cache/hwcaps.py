import logging
import struct
from sotools.dl_cache import _CacheHeader
from sotools.structure import Struct

# Appears as (uint32_t)-358342284 in glibc:/elf/cache.c
CACHE_EXTENSION_MAGIC = 3936625012


class CacheExtensionTag:
    TAG_GENERATOR = 0
    TAG_GLIBC_HWCAPS = 1
    COUNT = 2


class CacheExtensionSection(Struct):
    structure = [
        ('tag', 'uint32_t'),
        ('flags', 'uint32_t'),
        ('offset', 'uint32_t'),
        ('size', 'uint32_t'),
    ]
    size = 16


class CacheExtension(Struct):
    structure = [
        ('magic', 'uint32_t'),
        ('count', 'uint32_t'),
    ]
    size = 8


def glibc_hwcaps_string(data, entry):
    header = _CacheHeader.deserialize(data)

    extension_start = getattr(header, 'extension_offset', 0)

    if extension_start == 0:
        logging.debug(
            "Failed to retrieve hwcaps string for entry: header describes"
            " no extensions")
        return None

    extension_header = CacheExtension.deserialize(data[extension_start:])

    def parse_extensions():
        for i in range(extension_header.count):
            offset = extension_start + extension_header.size + i * CacheExtensionSection.size
            yield CacheExtensionSection.deserialize(data[offset:])

    # Filter out all non-hwcap related extensions to match the entry index
    # against the hwcaps only
    hwcap_extensions = list(
        filter(
            lambda x: getattr(x, 'tag', None) == CacheExtensionTag.
            TAG_GLIBC_HWCAPS, parse_extensions()))

    index = entry.hwcap & ((1 << 32) - 1)

    if not index < len(hwcap_extensions):
        logging.debug(
            "Error accessing hwcap extension: requested hwcap %d out of %d "
            "available", index, len(hwcap_extensions))
        return None

    hwcap_entry = hwcap_extensions[index]
    hwcap_data = data[hwcap_entry.offset:hwcap_entry.offset + hwcap_entry.size]
    hwcap_pointer = struct.unpack("I", hwcap_data)[0]

    terminator = data[hwcap_pointer:].find(0x0)
    b = struct.unpack_from(f"{terminator}s", data, hwcap_pointer)[0]

    return b.decode()
