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
