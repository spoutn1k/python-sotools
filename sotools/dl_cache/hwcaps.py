import struct
import logging
from sotools.dl_cache.dl_cache import _CacheHeader
from sotools.dl_cache.structure import (BinaryStruct, DATATYPES,
                                        deserialize_null_terminated_string)
from sotools.dl_cache.extensions import (CacheExtensionTag,
                                         CacheExtensionSection, CacheExtension)

# This bit in the hwcap field of struct file_entry_new indicates that
# the lower 32 bits contain an index into the
# cache_extension_tag_glibc_hwcaps section.  Older glibc versions do
# not know about this HWCAP bit, so they will ignore these
# entries.
DL_CACHE_HWCAP_EXTENSION = (1 << 62)

# The number of the ISA level bits in the upper 32 bits of the hwcap
# field.
DL_CACHE_HWCAP_ISA_LEVEL_COUNT = 10

# The mask of the ISA level bits in the hwcap field.
DL_CACHE_HWCAP_ISA_LEVEL_MASK = ((1 << DL_CACHE_HWCAP_ISA_LEVEL_COUNT) - 1)


def dl_cache_hwcap_extension(entry):
    hwcap_field = getattr(entry, 'hwcap', None)

    if hwcap_field is None:
        return False

    return ((hwcap_field >> 32) & ~DL_CACHE_HWCAP_ISA_LEVEL_MASK) == (
        DL_CACHE_HWCAP_EXTENSION >> 32)


class HWCAPSection(CacheExtensionSection):

    def __init__(self, section):
        super().__init__()

        # Copy to self the fields defined by the class
        for attribute, type_ in CacheExtensionSection.__structure__:
            # Fetch the default for this attribute type
            if type_ not in DATATYPES:
                raise NotImplementedError(
                    f"Unsupported field type for {attribute}: {type_}")
            _, _, default = DATATYPES[type_]

            # Access the field value then set it in self
            value = getattr(section, attribute, default())
            setattr(self, attribute, value)

    def string_value(self, data):
        hwcap_data = data[self.offset:self.offset + self.size]

        try:
            hwcap_pointer, = struct.unpack("I", hwcap_data)
        except struct.error as err:
            logging.error("Failed to retrieve hwcap string value: %s",
                          str(err))

        return deserialize_null_terminated_string(data[hwcap_pointer:])


def glibc_hwcaps_string(data, entry):
    header = _CacheHeader.deserialize(data)

    if not dl_cache_hwcap_extension(entry):
        logging.error("hwcap value of entry does not match a hwcap reference")
        return ""

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

    hwcap_entry = HWCAPSection(hwcap_extensions[index])

    return hwcap_entry.string_value(data)
