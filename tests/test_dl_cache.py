import unittest
from pathlib import Path
from sotools.dl_cache.structure import (
    BinaryStruct,
    deserialize_null_terminated_string,
)
from sotools.dl_cache.extensions import (
    CacheExtension,
    CacheExtensionSection,
    CacheExtensionTag,
    cache_extension_sections,
)
from sotools.dl_cache.dl_cache import (
    _CacheHeader,
    _CacheHeaderNew,
    _CacheHeaderOld,
    _CacheType,
    _FileEntryNew,
    _FileEntryOld,
    _cache_type,
)
from sotools.dl_cache.extensions.hwcaps import (
    HWCAPSection,
    dl_cache_hwcap_extension,
)
from sotools.dl_cache.flags import Flags
from sotools.dl_cache import (
    DynamicLinkerCache,
    _cache_libraries,
    _parse_cache,
    cache_libraries,
    get_generator,
    search_cache,
)

EMBEDDED_CACHE = f'{Path(__file__).parent}/assets/embedded.so.cache'
MODERN_CACHE = f'{Path(__file__).parent}/assets/modern.so.cache'
HWCAPS_CACHE = f'{Path(__file__).parent}/assets/with_hwcaps.so.cache'


class DLCacheTest(unittest.TestCase):

    def test_structure_bad_format(self):

        class MyStruct(BinaryStruct):
            pass

        with self.assertRaises(NotImplementedError):
            MyStruct.deserialize("Dummy string".encode())

        with self.assertRaises(NotImplementedError):
            BinaryStruct.sizeof(MyStruct)

    def test_format_detect(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            type_, offset = _cache_type(cache_file.read())

        self.assertEqual(type_, _CacheType.NEW_FORMAT)
        self.assertEqual(offset, 0)

        with open(EMBEDDED_CACHE, 'rb') as cache_file:
            type_, offset = _cache_type(cache_file.read())

        self.assertEqual(type_, _CacheType.NEW_FORMAT)
        self.assertNotEqual(offset, 0)

        type_, offset = _cache_type("This is not a cache".encode())

        self.assertEqual(type_, _CacheType.UNKNOWN)

    def test_class_routing(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        header = _CacheHeader.deserialize(cache_data)
        self.assertTrue(isinstance(header, _CacheHeaderNew))

        with open(EMBEDDED_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        _, offset = _cache_type(cache_data)

        header = _CacheHeader.deserialize(cache_data[:offset])
        self.assertTrue(isinstance(header, _CacheHeaderOld))

        header = _CacheHeader.deserialize(cache_data)
        self.assertTrue(isinstance(header, _CacheHeaderNew))

    def test_generated_repr(self):
        for cls in (_CacheHeaderNew, _CacheHeaderOld, _FileEntryNew,
                    _FileEntryOld):
            self.assertIn(cls.__name__, str(cls()))

            for (attribute, value) in cls.__structure__:
                if attribute is not None:
                    self.assertIn(attribute, str(cls()))

    def test_deserialize_bad_header(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        for i in range(24):
            with self.assertRaises(Exception):
                header = _CacheHeader.deserialize(cache_data[:i])

    def test_list_libraries(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        self.assertTrue(_cache_libraries(cache_data))

        with open(EMBEDDED_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        self.assertTrue(_cache_libraries(cache_data))

    def test_list_libraries_bad_cache(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        with self.assertRaises(Exception):
            libs = _cache_libraries(cache_data[:22])

        with self.assertRaises(Exception):
            libs = _cache_libraries(cache_data[:100])

    def test_wrapper(self):
        self.assertFalse(
            cache_libraries(cache_file=MODERN_CACHE,
                            arch_flags=Flags.FLAG_SPARC_LIB64))
        self.assertTrue(cache_libraries(cache_file=MODERN_CACHE))
        self.assertTrue(cache_libraries(cache_file=EMBEDDED_CACHE))

    def test_structure_sizeof(self):

        class TestByte(BinaryStruct):
            __structure__ = [('member', 'uint8_t')]

        class TestBytes(BinaryStruct):
            __structure__ = [('member', 'uint8_t'), ('other', 'uint8_t')]

        class TestInt(BinaryStruct):
            __structure__ = [('member', 'uint32_t')]

        class TestLong(BinaryStruct):
            __structure__ = [('member', 'uint64_t')]

        self.assertEqual(BinaryStruct.sizeof(TestByte), 1)
        self.assertEqual(BinaryStruct.sizeof(TestBytes), 2)
        self.assertEqual(BinaryStruct.sizeof(TestInt), 4)
        self.assertEqual(BinaryStruct.sizeof(TestLong), 8)

        class TestPadding(BinaryStruct):
            __structure__ = [('member', 'uint64_t'), (None, 24),
                             ('other', 'uint32_t')]

        self.assertEqual(BinaryStruct.sizeof(TestPadding), 36)

        class TestPaddingBadFormat(BinaryStruct):
            __structure__ = [('member', 'uint64_t'), (None, None),
                             ('other', 'uint32_t')]

        self.assertEqual(BinaryStruct.sizeof(TestPaddingBadFormat), 12)

    def test_structure_deserialize(self):

        class TestStruct(BinaryStruct):
            __structure__ = [('a', 'uint32_t'), ('b', 'uint8_t')]

        parsed = TestStruct.deserialize(
            int(10).to_bytes(4, 'big') + int(254).to_bytes(1, 'big'))
        self.assertIsInstance(parsed, TestStruct)

        with self.assertRaises(NotImplementedError):
            parsed = TestStruct.deserialize("test")

    def test_deserialize_header(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        header = _CacheHeader.deserialize(cache_data)

        self.assertTrue(header.nlibs)

    def test_deserialize_entry(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        header = _CacheHeader.deserialize(cache_data)
        header_size = BinaryStruct.sizeof(header.__class__)
        entry_type = header.__class__.entry_type

        entry = entry_type.deserialize(cache_data[header_size:])
        self.assertNotEqual(entry.key, 0)
        self.assertNotEqual(entry.value, 0)
        self.assertNotEqual(entry.flags, 0)

        self.assertLess(entry.key, header.extension_offset)
        self.assertLess(entry.value, header.extension_offset)

    def test_deserialize_extension_header(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        header = _CacheHeader.deserialize(cache_data)
        extension_header = CacheExtension.deserialize(
            cache_data[header.extension_offset:])

        self.assertNotEqual(extension_header.count, 0)

    def test_deserialize_extension_sections(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        header = _CacheHeader.deserialize(cache_data)

        for section in cache_extension_sections(
                cache_data[header.offset + header.extension_offset:]):
            self.assertIn(
                section.tag, {
                    CacheExtensionTag.TAG_GENERATOR,
                    CacheExtensionTag.TAG_GLIBC_HWCAPS
                })
            self.assertNotEqual(section.offset, 0)
            self.assertNotEqual(section.size, 0)

    def test_deserialize_nts(self):
        string = "I am a string"
        data = f"{string}\0".encode()

        self.assertEqual(deserialize_null_terminated_string(data), string)
        self.assertEqual(deserialize_null_terminated_string(string.encode()),
                         "")

    def test_get_hwcap_string(self):
        with open(HWCAPS_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        header = _CacheHeader.deserialize(cache_data)

        for section in cache_extension_sections(
                cache_data[header.offset + header.extension_offset:]):
            if section.tag == CacheExtensionTag.TAG_GLIBC_HWCAPS:
                hwcap_section = HWCAPSection(section)
                self.assertTrue(hwcap_section.string_value(cache_data))

        badlength = HWCAPSection(CacheExtensionSection())
        HWCAPSection.offset = 0
        HWCAPSection.size = 40

        self.assertEqual(
            badlength.string_value("Not an int, too short".encode()), "")

    def test_assert_hwcap_reference(self):
        entry = _FileEntryNew()

        entry.hwcap = 4611686018427387904
        self.assertTrue(dl_cache_hwcap_extension(entry))

        entry.hwcap = 0
        self.assertFalse(dl_cache_hwcap_extension(entry))

        entry.hwcap = 1
        self.assertFalse(dl_cache_hwcap_extension(entry))

        entry = _FileEntryOld()
        self.assertFalse(dl_cache_hwcap_extension(entry))

    def test_parse_hwcap(self):
        cache = _parse_cache(HWCAPS_CACHE)

        self.assertTrue(set(filter(lambda x: x.hwcaps, cache.entries)))

    def test_extension_generator(self):
        with open(MODERN_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        self.assertTrue(get_generator(cache_data))

        with open(EMBEDDED_CACHE, 'rb') as cache_file:
            cache_data = cache_file.read()

        self.assertIsNone(get_generator(cache_data))

    def test_search_cache(self):
        self.assertTrue(search_cache('libc.so.6', MODERN_CACHE))
        self.assertIsNone(search_cache('notalib.so', MODERN_CACHE))
        self.assertIsNone(
            search_cache('libc.so.6', MODERN_CACHE, Flags.FLAG_POWERPC_LIB64))

    def test_parse_cache(self):
        self.assertIsNone(_parse_cache('/not/a/file'))
        self.assertIsNone(_parse_cache(__file__))
        self.assertIsInstance(_parse_cache(EMBEDDED_CACHE), DynamicLinkerCache)
        self.assertIsInstance(_parse_cache(MODERN_CACHE), DynamicLinkerCache)
        self.assertIsInstance(_parse_cache(HWCAPS_CACHE), DynamicLinkerCache)
