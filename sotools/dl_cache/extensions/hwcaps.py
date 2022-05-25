import struct
import logging
from sotools.dl_cache.structure import (DATATYPES,
                                        deserialize_null_terminated_string)
from sotools.dl_cache.extensions import CacheExtensionSection

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

    def __init__(self, section=None):
        super().__init__()

        # Copy to self the fields defined by the class
        for attribute, type_ in CacheExtensionSection.__structure__:
            # Fetch the default for this attribute type
            _, _, default = DATATYPES.get(type_, int)

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
            return ""

        return deserialize_null_terminated_string(data[hwcap_pointer:])
