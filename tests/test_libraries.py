import unittest
from sotools.linker import resolve
from sotools.libraryset import Library

class LibraryTest(unittest.TestCase):
    def test_library_bad_object(self):
        with self.assertRaises(Exception):
            lib = Library.from_path("/tmp/lib.so")

    @unittest.skipIf(not resolve('libm.so.6') or not resolve('libc.so.6'), "No library to test with")
    def test_library_eq_library(self):
        sample = Library.from_path(resolve('libm.so.6'))
        other = Library.from_path(resolve('libm.so.6'))

        different = Library.from_path(resolve('libc.so.6'))

        self.assertEqual(sample, other)
        self.assertEqual(other, sample)
        self.assertNotEqual(sample, different)
        self.assertNotEqual(other, different)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_library_eq_any(self):
        sample = Library.from_path(resolve('libm.so.6'))

        self.assertNotEqual(sample, 'libm.so.6')
        self.assertNotEqual('libm.so.6', sample)
