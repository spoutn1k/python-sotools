from sotools.dl_cache.structure import BinaryStruct

# Appears as (uint32_t)-358342284 in glibc:/elf/cache.c
CACHE_EXTENSION_MAGIC = 3936625012


class CacheExtensionTag:
    TAG_GENERATOR = 0
    TAG_GLIBC_HWCAPS = 1
    COUNT = 2


class CacheExtensionSection(BinaryStruct):
    __structure__ = [
        ('tag', 'uint32_t'),
        ('flags', 'uint32_t'),
        ('offset', 'uint32_t'),
        ('size', 'uint32_t'),
    ]


class CacheExtension(BinaryStruct):
    __structure__ = [
        ('magic', 'uint32_t'),
        ('count', 'uint32_t'),
    ]


def cache_extension_sections(data: bytes):

    extension_header = CacheExtension.deserialize(data)

    header_size = BinaryStruct.sizeof(CacheExtension)
    section_size = BinaryStruct.sizeof(CacheExtensionSection)

    def parse_sections():
        for i in range(extension_header.count):
            offset = header_size + i * section_size
            yield CacheExtensionSection.deserialize(data[offset:])

    return list(parse_sections())
