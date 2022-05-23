import struct

DATATYPES = {
    # Datatypes used to describe the binary structure of the classes defined
    # below. The first field is the byte size of the member, the second field
    # is the format string to pass to `struct.unpack` when deserializing, and
    # the last field is the default initializer to use.
    'uint8_t': (1, 'B', int),
    'int32_t': (4, 'i', int),
    'uint32_t': (4, 'I', int),
    'uint64_t': (8, 'Q', int),
}


class Struct:

    def __init__(self):
        for (attribute, type_) in self.__class__.structure:
            if attribute is None:
                continue
            _, _, default = DATATYPES.get(type_)

            setattr(self, attribute, default())

    @classmethod
    def deserialize(cls, data: bytes):
        serialized = 0
        entry = cls()

        for (attribute, type_) in cls.structure:
            if attribute is None:
                serialized += type_
                continue

            size, format_, _ = DATATYPES.get(type_)

            try:
                value = struct.unpack(f'<{format_}',
                                      data[serialized:serialized + size])[0]
            except struct.error as err:
                raise Exception(
                    f"Error deserializing field {attribute}") from err

            setattr(entry, attribute, value)
            serialized = serialized + size

        return entry

    def __repr__(self):

        def _format_attributes():
            for (attribute, _) in getattr(self.__class__, 'structure', []):
                if attribute is not None:
                    yield f"{attribute}={getattr(self, attribute, None)}"

        return f"{self.__class__.__name__}: " + ", ".join(_format_attributes())
