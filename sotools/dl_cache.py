import logging
import struct
from functools import lru_cache

DATATYPES = {
    'int32_t': (4, 'i', int),
    'uint32_t': (4, 'I', int),
    'uint64_t': (8, 'Q', int),
}


class _CacheType:
    """
    Used as an enum to differentiate cache types
    """
    UNKNOWN = 0x0
    NEW_FORMAT = 0x1
    OLD_FORMAT = 0x2


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

        def _format(data):
            attribute, _ = data
            if attribute is None:
                return None
            return f"{attribute}={getattr(self, attribute, None)}"

        return f"{self.__class__.__name__}: " + ", ".join(
            filter(None, map(_format, self.__class__.structure)))


class _FileEntryOld(Struct):
    structure = [('flags', 'int32_t'), ('key', 'uint32_t'),
                 ('value', 'uint32_t')]
    size = 12


class _FileEntryNew(Struct):
    structure = [('flags', 'int32_t'), ('key', 'uint32_t'),
                 ('value', 'uint32_t')]
    size = 24


class _CacheHeaderOld(Struct):
    magic = "ld.so-1.7.0".encode()
    structure = [(None, 12), ('nlibs', 'uint32_t')]
    size = 16
    entry_type = _FileEntryOld


class _CacheHeaderNew(Struct):
    __cachemagic_new = "glibc-ld.so.cache".encode()
    __cache_version = "1.1".encode()
    magic = __cachemagic_new + __cache_version
    structure = [(None, 20), ('nlibs', 'uint32_t')]
    size = 48
    entry_type = _FileEntryNew


def _format_error(*args, **kwargs):
    raise Exception("Data does not match a dynamic library cache")


class _CacheHeader:
    methods = {
        _CacheType.UNKNOWN: _format_error,
        _CacheType.NEW_FORMAT: _CacheHeaderNew.deserialize,
        _CacheType.OLD_FORMAT: _CacheHeaderOld.deserialize
    }

    @classmethod
    def deserialize(cls, data: bytes):
        cache_format, offset = _cache_type(data)

        header = cls.methods.get(cache_format, _format_error)(data[offset:])
        header.offset = offset

        return header


def _cache_type(data: bytes):
    """ -> tuple[int]
    Determine the type of cache (from_CacheType) and the offset
    to start reading it from
    """

    if data[:len(_CacheHeaderNew.magic)] == _CacheHeaderNew.magic:
        return (_CacheType.NEW_FORMAT, 0)
    elif data[:len(_CacheHeaderOld.magic)] == _CacheHeaderOld.magic:
        # We do not have access to __alignof__, so search for magic
        offset = data.find(_CacheHeaderNew.magic)
        if offset != -1:
            return (_CacheType.NEW_FORMAT, offset)
        return (_CacheType.OLD_FORMAT, 0)

    return (_CacheType.UNKNOWN, 0)


def _cache_libraries(data: bytes):
    """ -> dict[str, str]
    From bytes, extract a header, then library entries and finally lookup
    the names associated with each entry
    """
    header = _CacheHeader.deserialize(data)

    def _entries(data: bytes) -> list:
        """
        Generate a list of entries from the type defined in the header
        """
        et = header.__class__.entry_type

        for index in range(header.nlibs):
            offset = header.offset + header.__class__.size + index * et.size
            entry = et.deserialize(data[offset:offset + et.size])
            yield entry

    def _lookup(entry):
        """
        Translate string references to strings
        """
        terminator = data[header.offset + entry.key:].find(0x0)
        key = struct.unpack_from(f"{terminator}s", data,
                                 header.offset + entry.key)[0]

        terminator = data[header.offset + entry.value:].find(0x0)
        value = struct.unpack_from(f"{terminator}s", data,
                                   header.offset + entry.value)[0]

        return (key.decode(), value.decode())

    try:
        return dict(map(_lookup, _entries(data)))
    except struct.error as err:
        raise Exception("Failed retrieving data from cache") from err


@lru_cache()
def host_libraries():
    with open('/etc/ld.so.cache', 'rb') as cache_file:
        cache = cache_file.read()

    try:
        libs = _cache_libraries(cache)
    except Exception as err:
        logging.debug("DLCache parsing failed: %s", str(err))
        libs = {}

    return libs
