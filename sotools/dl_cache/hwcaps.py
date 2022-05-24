import struct
import logging
from sotools.dl_cache.dl_cache import _CacheHeader
from sotools.dl_cache.structure import (BinaryStruct,
                                        deserialize_null_terminated_string)
from sotools.dl_cache.extensions import (CacheExtensionTag,
                                         CacheExtensionSection, CacheExtension)


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
        header_size = BinaryStruct.sizeof(CacheExtension)
        section_size = BinaryStruct.sizeof(CacheExtensionSection)
        for i in range(extension_header.count):
            offset = extension_start + header_size + i * section_size
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

    return deserialize_null_terminated_string(data[hwcap_pointer:])
