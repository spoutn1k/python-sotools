import unittest
from sotools.linker import resolve
from sotools.libraryset import Library

class LibraryTest(unittest.TestCase):
    def test_library_bad_object(self):
        lib = Library(file="/tmp/lib.so")

        self.assertFalse(lib.soname)

    def test_library_bad_params(self):
        lib = Library(file=None, soname="")

        self.assertFalse(lib.soname)

    @unittest.skipIf(not resolve('libm.so.6') or not resolve('libc.so.6'), "No library to test with")
    def test_library_eq_library(self):
        with open(resolve('libm.so.6'), 'rb') as file:
            sample = Library(file=file)
            other = Library(file=file)

        with open(resolve('libc.so.6'), 'rb') as file:
            different = Library(file=file)

        self.assertEqual(sample, other)
        self.assertEqual(other, sample)
        self.assertNotEqual(sample, different)
        self.assertNotEqual(other, different)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_library_eq_library(self):
        with open(resolve('libm.so.6'), 'rb') as file:
            sample = Library(file=file)

        self.assertNotEqual(sample, 'libm.so.6')
        self.assertNotEqual('libm.so.6', sample)
