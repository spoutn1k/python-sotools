from sotools.dl_cache.structure import DATATYPES
from sotools.dl_cache.extensions import CacheExtensionSection


class GeneratorSection(CacheExtensionSection):

    def __init__(self, section):
        super().__init__()

        # Copy to self the fields defined by the class
        for attribute, type_ in CacheExtensionSection.__structure__:
            # Fetch the default for this attribute type
            _, _, default = DATATYPES.get(type_, int)

            # Access the field value then set it in self
            value = getattr(section, attribute, default())
            setattr(self, attribute, value)

    def string_value(self, data):
        return data[self.offset:self.offset + self.size].decode()
