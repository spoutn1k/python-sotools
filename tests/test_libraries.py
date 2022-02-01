import os
import pathlib
import unittest
from shutil import which
from sotools import host_libraries, resolve, LibrarySet, Library, is_elf, library_links


class LibraryTest(unittest.TestCase):
    def test_host_libraries(self):
        self.assertNotEqual(host_libraries(), {})

    @unittest.skipIf(not which('ls'), "No binary to test with")
    def test_ldd(self):
        ls_bin = which('ls')
        libraries = ldd(ls_bin)

        self.assertTrue({'libc.so.6', 'linker'} < set(libraries.keys()))

    @unittest.skipIf(not which('ls'), "No binary to test with")
    def test_resolving(self):
        """
        Check ldd output equals resolve output
        """
        ls_bin = which('ls')
        libraries = ldd(ls_bin)

        dependencies = set(libraries.keys())
        dependencies.difference_update({'linker'})

        for soname in dependencies:
            self.assertEqual(os.path.realpath(libraries[soname]['path']),
                             resolve(soname))

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_links(self):
        with open(resolve('libm.so.6'), 'rb') as file:
            target = Library(file=file)

        links = library_links(target)
        for path in links:
            self.assertEqual(os.path.realpath(path),
                             os.path.realpath(target.binary_path))

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

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_is_elf(self):
        self.assertFalse(is_elf('/proc/meminfo'))
        self.assertFalse(is_elf('/'))
        self.assertTrue(is_elf(resolve('libm.so.6')))

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_library_links(self):
        with open(resolve('libm.so.6'), 'rb') as file:
            sample = Library(file=file)

        links = library_links(sample)

        self.assertGreater(len(links), 1)
        for path in links:
            self.assertEqual(os.path.realpath(path), sample.binary_path)

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
