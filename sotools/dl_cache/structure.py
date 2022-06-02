import struct
import logging

DATATYPES = {
    # Datatypes used to describe the binary structure of the classes defined
    # to interpret the binary data. The first field is the byte size of the
    # member, the second field is the format string to pass to `struct.unpack`
    # when deserializing, and the last field is the default initializer to use.
    'uint8_t': (1, 'B', int),
    'int32_t': (4, 'i', int),
    'uint32_t': (4, 'I', int),
    'uint64_t': (8, 'Q', int),
}


class BinaryStruct:

    def sizeof(cls):
        # Check defined information
        hardcoded_size = getattr(cls, '_sizeof', None)
        structure = getattr(cls, '__structure__', None)

        # Return hardcoded size if it exists
        if hardcoded_size is not None:
            return hardcoded_size

        # Ensure the __structure__ attribute exists
        if structure is None:
            raise NotImplementedError(
                "Attempting to access size of class with no __structure__"
                f" field ({cls.__name__})")

        struct_size = 0

        # Resolve all members and cumulate their sizes
        for (attribute, type_) in structure:
            if attribute is None:
                if isinstance(type_, int):
                    struct_size += type_
                continue

            attr_size, _, _ = DATATYPES.get(type_)
            struct_size += attr_size

        return struct_size

    def __init__(self):
        for (attribute, type_) in self.__class__.__structure__:
            if attribute is None:
                continue

            _, _, default = DATATYPES.get(type_)

            setattr(self, attribute, default())

    @classmethod
    def deserialize(cls, data: bytes):
        if not isinstance(data, bytes):
            raise NotImplementedError(
                f"Unsupported value for deserialization buffer: {type(data)}")

        if getattr(cls, '__structure__', None) is None:
            raise NotImplementedError(
                "Attempting to deserialize class with no __structure__"
                f" field ({cls.__name__})")

        serialized = 0
        entry = cls()

        for (attribute, type_) in cls.__structure__:
            if attribute is None:
                serialized += type_
                continue

            size, format_, _ = DATATYPES.get(type_)

            try:
                value = struct.unpack(f'<{format_}',
                                      data[serialized:serialized + size])[0]
            except struct.error as err:
                raise Exception(
                    f"Error deserializing field {attribute} from object"
                    f" {cls.__name__}") from err

            setattr(entry, attribute, value)
            serialized = serialized + size

        return entry

    def __repr__(self):

        def _format_attributes():
            for (attribute, _) in getattr(self.__class__, '__structure__', []):
                if attribute is not None:
                    yield f"{attribute}={getattr(self, attribute, None)}"

        return f"{self.__class__.__name__}: " + ", ".join(_format_attributes())


def deserialize_null_terminated_string(data: bytes):
    terminator = data.find(0x0)

    if terminator == -1:
        logging.debug("Failed to find null byte in buffer")
        return ""

    return data[:terminator].decode(errors='replace')
