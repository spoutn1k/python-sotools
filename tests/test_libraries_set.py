from pathlib import Path
import unittest
from sotools.libraryset import LibrarySet, Library
from sotools.linker import resolve


class LibrarySetTest(unittest.TestCase):

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set(self):
        libset = LibrarySet([Library.from_path(resolve('libm.so.6'))])

        self.assertEqual(len(libset), 1)
        self.assertSetEqual(libset.sonames, {'libm.so.6'})

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set_resolve(self):
        libset = LibrarySet([Library.from_path(resolve('libm.so.6'))])

        libset = libset.resolve()

        self.assertGreater(len(libset), 1)
        self.assertTrue(libset.sonames > {'libm.so.6', 'libc.so.6'})

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set_missing(self):
        libset = LibrarySet([Library.from_path(resolve('libm.so.6'))])

        self.assertIn('libc.so.6', libset.missing_libraries)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set_top(self):
        libset = LibrarySet([Library.from_path(resolve('libm.so.6'))])

        self.assertIn('libm.so.6', libset.top_level.sonames)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_create_from_soname(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertTrue(libset.complete)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_create_from_str_path(self):
        libset = LibrarySet.create_from([resolve('libm.so.6')])

        self.assertTrue(libset.complete)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_create_from_pathlib_path(self):
        libset = LibrarySet.create_from([Path(resolve('libm.so.6'))])

        self.assertTrue(libset.complete)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_get_glib(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertTrue(libset.glib)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_get_linkers(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertTrue(libset.linkers)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_get_outdated(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertFalse(libset.outdated_libraries)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_ldd(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        output = libset.ldd_format()

        for line in output:
            self.assertRegex(line, ".*.so.* => /.*")

    def test_ldd(self):
        lib = Library()
        lib.soname = 'libdummy.so.256'
        libset = LibrarySet([lib])

        output = libset.ldd_format()

        for line in output:
            self.assertRegex(line, ".*.so.* => not found")

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_escape_soname(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertFalse(libset.find('libc++'))

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_escape_soname(self):
        libset = LibrarySet.create_from(['libm.so.6'])

        self.assertFalse(libset.find('libc++'))

    def test_create_from_bad_input(self):
        with self.assertRaises(Exception):
            LibrarySet.create_from(range(10))

        with self.assertRaises(Exception):
            LibrarySet.create_from([None])

        with self.assertRaises(Exception):
            LibrarySet.create_from(['libnotalib.so'])

    def test_add_junk(self):
        with self.assertRaises(Exception):
            LibrarySet().add(1)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_set(self):
        libset = LibrarySet()

        lib1 = Library()
        lib1.soname = "libnotalib.so"
        lib2 = Library()
        lib2.soname = "libnotalib.so"
        lib2.binary_path = "/tmp/notalib.so"

        libset.add(lib1)
        libset.add(lib2)

        self.assertEqual(len(libset), 1)
        saved_lib = libset.pop()
        self.assertEqual(saved_lib.binary_path, "/tmp/notalib.so")
