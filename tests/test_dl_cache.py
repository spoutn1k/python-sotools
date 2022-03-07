import unittest
from pathlib import Path
from sotools.dl_cache import (_cache_type, _cache_libraries, _CacheType, _CacheHeader, _CacheHeaderNew, _CacheHeaderOld)

EMBEDDED_CACHE = f'{Path(__file__).parent}/assets/embedded.so.cache'
MODERN_CACHE = f'{Path(__file__).parent}/assets/modern.so.cache'


class DLCacheTest(unittest.TestCase):

    def test_type_detect(self):
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

    def test_generation(self):
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
