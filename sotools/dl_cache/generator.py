import struct
import logging
from sotools.dl_cache.structure import DATATYPES
from sotools.dl_cache.extensions import CacheExtensionSection


class GeneratorSection(CacheExtensionSection):

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
        return data[self.offset:self.offset + self.size].decode()
