from sotools.dl_cache.structure import BinaryStruct, deserialize_null_terminated_string


class _CacheType:
    """
    Used as an enum to differentiate cache types
    """
    UNKNOWN = 0x0
    NEW_FORMAT = 0x1
    OLD_FORMAT = 0x2


class _FileEntryOld(BinaryStruct):
    __structure__ = [('flags', 'int32_t'), ('key', 'uint32_t'),
                     ('value', 'uint32_t')]


class _FileEntryNew(BinaryStruct):
    __structure__ = [('flags', 'int32_t'), ('key', 'uint32_t'),
                     ('value', 'uint32_t'), ('osversion', 'uint32_t'),
                     ('hwcap', 'uint64_t')]


class _CacheHeaderOld(BinaryStruct):
    magic = "ld.so-1.7.0".encode()
    __structure__ = [(None, 12), ('nlibs', 'uint32_t')]
    entry_type = _FileEntryOld


class _CacheHeaderNew(BinaryStruct):
    __cachemagic_new = "glibc-ld.so.cache".encode()
    __cache_version = "1.1".encode()
    magic = __cachemagic_new + __cache_version
    __structure__ = [
        (None, 20),  # Cache magic and version string
        ('nlibs', 'uint32_t'),
        ('len_strings', 'uint32_t'),
        ('flags', 'uint8_t'),
        (None, 3),
        ('extension_offset', 'uint32_t'),
    ]
    _sizeof = 48
    entry_type = _FileEntryNew


def _format_error(*args, **kwargs):
    raise Exception("Data does not match a dynamic library cache")


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
        header_size = BinaryStruct.sizeof(header.__class__)
        entry_type = header.__class__.entry_type
        entry_size = BinaryStruct.sizeof(entry_type)

        for index in range(header.nlibs):
            offset = header.offset + header_size + index * entry_size
            entry = entry_type.deserialize(data[offset:offset + entry_size])
            yield entry

    def _lookup(entry):
        """
        Translate string references to strings
        """
        lookup = deserialize_null_terminated_string
        key = lookup(data[header.offset + entry.key:])
        value = lookup(data[header.offset + entry.value:])

        return (key, (entry.flags, value))

    return list(map(_lookup, _entries(data)))
