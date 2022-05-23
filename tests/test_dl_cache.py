import unittest
from pathlib import Path
from sotools.dl_cache.dl_cache import (_cache_type, _cache_libraries,
                                       _CacheType, _CacheHeader,
                                       _CacheHeaderNew, _CacheHeaderOld,
                                       _FileEntryNew, _FileEntryOld)
from sotools.dl_cache import host_libraries

EMBEDDED_CACHE = f'{Path(__file__).parent}/assets/embedded.so.cache'
MODERN_CACHE = f'{Path(__file__).parent}/assets/modern.so.cache'


class DLCacheTest(unittest.TestCase):

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
        self.assertTrue(host_libraries())
