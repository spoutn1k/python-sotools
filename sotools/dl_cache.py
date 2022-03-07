import struct
from functools import lru_cache

CACHEMAGIC = "ld.so-1.7.0".encode()

CACHEMAGIC_NEW = "glibc-ld.so.cache".encode()
CACHE_VERSION = "1.1".encode()
CACHEMAGIC_VERSION_NEW = CACHEMAGIC_NEW + CACHE_VERSION


class _CacheType:
    """
    Used as an enum to differentiate cache types
    """
    UNKNOWN = 0x0
    NEW_FORMAT = 0x1
    OLD_FORMAT = 0x2


class _FileEntryOld:
    size = 12

    def __init__(self):
        self.flags = 0  # int32t
        self.key = 0  # uint32t
        self.value = 0  # uint32t

    @classmethod
    def deserialize(cls, data: bytes):
        entry = cls()

        try:
            entry.flags = struct.unpack('<i', data[0:4])[0]
            entry.key = struct.unpack('<I', data[4:8])[0]
            entry.value = struct.unpack('<I', data[8:12])[0]
        except struct.error:
            entry = cls()

        return entry

    def __repr__(self):
        return (f"{self.__class__.__name__}: {self.key=} => "
                f"{self.value=}, {self.flags=}")


class _FileEntryNew:
    size = 24

    def __init__(self):
        self.flags = 0  # int32t
        self.key = 0  # uint32t
        self.value = 0  # uint32t
        # self.os_version = 0 # uint32t
        # self.hwcap = 0      # uint64t

    @classmethod
    def deserialize(cls, data: bytes):
        entry = cls()

        try:
            entry.flags = struct.unpack('<i', data[0:4])[0]
            entry.key = struct.unpack('<I', data[4:8])[0]
            entry.value = struct.unpack('<I', data[8:12])[0]
            # entry.os_version = struct.unpack('<I', data[12:16])[0]
            # entry.hwcap = struct.unpack('<Q', data[16:24])[0]
        except struct.error:
            entry = cls()

        return entry

    def __repr__(self):
        return (f"{self.__class__.__name__}: {self.key=} => "
                f"{self.value=}, {self.flags=}")


class _CacheHeaderOld:
    size = 16
    entry_type = _FileEntryOld

    def __init__(self):
        # magic: 12 bytes
        self.nlibs = 0

    @classmethod
    def deserialize(cls, data: bytes):
        cache = cls()

        try:
            cache.nlibs = struct.unpack('<I', data[12:16])[0]
        except struct.error:
            cache = cls()

        return cache


class _CacheHeaderNew:
    size = 48
    entry_type = _FileEntryNew

    def __init__(self):
        # magic: 20 bytes
        self.nlibs = 0
        self.len_strings = 0
        self.flags = 0
        # unused: 3 bytes
        # self.extension_offset = 0
        # unused: 12 bytes

    @classmethod
    def deserialize(cls, data: bytes):
        cache = cls()

        try:
            cache.flags = data[28]

            cache.nlibs = struct.unpack('<I', data[20:24])[0]
            cache.len_strings = struct.unpack('<I', data[24:28])[0]

            # cache.extension_offset = struct.unpack('<I', data[32:36])[0]
        except struct.error:
            cache = cls()

        return cache

    def __repr__(self):
        return (
            f"{self.__class__.__name__}: {self.nlibs=}; "
            f"{self.len_strings=}; {self.extension_offset=}; {self.flags=}")


def _format_error():
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

        if cache_format not in cls.methods:
            raise Exception(f"Unrecognised format for cache: {cache_format}")

        header = cls.methods.get(cache_format, None)(data[offset:])
        header.offset = offset

        return header


def _cache_type(data: bytes):
    """ -> tuple[int]
    Determine the type of cache (from_CacheType) and the offset
    to start reading it from
    """

    if data[:len(CACHEMAGIC_VERSION_NEW)] == CACHEMAGIC_VERSION_NEW:
        return (_CacheType.NEW_FORMAT, 0)
    elif data[:len(CACHEMAGIC)] == CACHEMAGIC:
        # We do not have access to __alignof__, so search for magic
        offset = data.find(CACHEMAGIC_VERSION_NEW)
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

    return dict(map(_lookup, _entries(data)))


@lru_cache
def host_libraries():
    with open('/etc/ld.so.cache', 'rb') as cache_file:
        cache = cache_file.read()

    return _cache_libraries(cache)
