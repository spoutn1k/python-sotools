import unittest
from sotools.libraryset import LibrarySet, Library
from sotools.linker import resolve


class LibrarySetTest(unittest.TestCase):

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set(self):
        libset = LibrarySet()

        with open(resolve('libm.so.6'), 'rb') as file:
            libset.add(Library(file=file))

        self.assertEqual(len(libset), 1)
        self.assertSetEqual(libset.sonames, {'libm.so.6'})

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set_resolve(self):
        libset = LibrarySet()

        with open(resolve('libm.so.6'), 'rb') as file:
            libset.add(Library(file=file))

        libset = libset.resolve()

        self.assertGreater(len(libset), 1)
        self.assertTrue(libset.sonames > {'libm.so.6', 'libc.so.6'})

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set_missing(self):
        libset = LibrarySet()

        with open(resolve('libm.so.6'), 'rb') as file:
            libset.add(Library(file=file))

        self.assertIn('libc.so.6', libset.missing_libraries)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set_top(self):
        libset = LibrarySet()

        with open(resolve('libm.so.6'), 'rb') as file:
            libset.add(Library(file=file))

        self.assertIn('libm.so.6', libset.top_level.sonames)

    def test_create_from_soname(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertTrue(libset.complete)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_create_from_path(self):
        libset = LibrarySet.create_from([resolve('libm.so.6')])

        self.assertTrue(libset.complete)

    def test_escape_soname(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertFalse(libset.find('libc++'))
