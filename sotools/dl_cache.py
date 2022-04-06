import logging
import struct
from functools import lru_cache


class Flags(int):
    FLAG_ANY = -1

    FLAG_TYPE_MASK = 0x00ff
    FLAG_LIBC4 = 0x0000
    FLAG_ELF = 0x0001
    FLAG_ELF_LIBC5 = 0x0002
    FLAG_ELF_LIBC6 = 0x0003

    FLAG_REQUIRED_MASK = 0xff00
    FLAG_SPARC_LIB64 = 0x0100
    FLAG_IA64_LIB64 = 0x0200
    FLAG_X8664_LIB64 = 0x0300
    FLAG_S390_LIB64 = 0x0400
    FLAG_POWERPC_LIB64 = 0x0500
    FLAG_MIPS64_LIBN32 = 0x0600
    FLAG_MIPS64_LIBN64 = 0x0700
    FLAG_X8664_LIBX32 = 0x0800
    FLAG_ARM_LIBHF = 0x0900
    FLAG_AARCH64_LIB64 = 0x0a00
    FLAG_ARM_LIBSF = 0x0b00
    FLAG_MIPS_LIB32_NAN2008 = 0x0c00
    FLAG_MIPS64_LIBN32_NAN2008 = 0x0d00
    FLAG_MIPS64_LIBN64_NAN2008 = 0x0e00
    FLAG_RISCV_FLOAT_ABI_SOFT = 0x0f00
    FLAG_RISCV_FLOAT_ABI_DOUBLE = 0x1000

    TYPES_DESCR = {
        FLAG_LIBC4: "libc4",
        FLAG_ELF: "ELF",
        FLAG_ELF_LIBC5: "libc5",
        FLAG_ELF_LIBC6: "libc6",
    }

    REQUIRED_DESCR = {
        0: '',
        FLAG_SPARC_LIB64: ",64bit",
        FLAG_IA64_LIB64: ",IA-64",
        FLAG_X8664_LIB64: ",x86-64",
        FLAG_S390_LIB64: ",64bit",
        FLAG_POWERPC_LIB64: ",64bit",
        FLAG_MIPS64_LIBN32: ",N32",
        FLAG_MIPS64_LIBN64: ",64bit",
        FLAG_X8664_LIBX32: ",x32",
        FLAG_ARM_LIBHF: ",hard-float",
        FLAG_AARCH64_LIB64: ",AArch64",
        FLAG_ARM_LIBSF: ",soft-float",
        FLAG_MIPS_LIB32_NAN2008: ",nan2008",
        FLAG_MIPS64_LIBN32_NAN2008: ",N32,nan2008",
        FLAG_MIPS64_LIBN64_NAN2008: ",64bit,nan2008",
        FLAG_RISCV_FLOAT_ABI_SOFT: ",soft-float",
        FLAG_RISCV_FLOAT_ABI_DOUBLE: ",double-float",
    }

    def __str__(self):
        type_flag = self & Flags.FLAG_TYPE_MASK
        required_flag = self & Flags.FLAG_REQUIRED_MASK

        type_str = Flags.TYPES_DESCR.get(type_flag, 'unknown')
        required_str = Flags.REQUIRED_DESCR.get(required_flag,
                                                str(required_flag))

        return f"{type_str}{required_str}"


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


class CacheElement:
    """
    Functionnally identical to FileEntry with the references resolved and
    helper functions
    """

    fields = {
        'soname': str,
        'path': str,
        'flags': Flags,
    }

    def __init__(self, *args, **kwargs):
        for field, initializer in self.__class__.fields.items():
            setattr(self, field, initializer(kwargs.get(field, initializer())))

    def __hash__(self):
        return hash(self.soname + str(self.flags))

    def __repr__(self):
        return f"{self.soname} ({self.flags}) => {self.path}"


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

        return CacheElement(soname=key.decode(),
                            path=value.decode(),
                            flags=entry.flags)

    try:
        return set(map(_lookup, _entries(data)))
    except struct.error as err:
        raise Exception("Failed retrieving data from cache") from err


@lru_cache()
def host_libraries():
    """
    Returns a dictionary with the contents of /etc/ld.so.cache
    Can be used to assume what libraries are installed on the system and where
    The keys are libraries' sonames; the values are the paths at which the
    corresponding shared object can be found
    """
    with open('/etc/ld.so.cache', 'rb') as cache_file:
        cache = cache_file.read()

    try:
        libs = _cache_libraries(cache)
    except Exception as err:
        #logging.debug("DLCache parsing failed: %s", str(err))
        print("DLCache parsing failed: %s", str(err))
        libs = {}

    return libs
