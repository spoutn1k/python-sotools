from pathlib import Path
import unittest
from shutil import which
from sotools import is_elf, library_links
from sotools.ldd import ldd
from sotools.libraryset import LibrarySet, Library
from sotools.linker import resolve


class ToolsTest(unittest.TestCase):

    @unittest.skipIf(not which('ls'), "No binary to test with")
    def test_ldd(self):
        ls_bin = which('ls')
        libraries = ldd(ls_bin)

        self.assertIn('libc.so.6', libraries.sonames)

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_library_links(self):
        target = Library.from_path(resolve('libm.so.6'))

        links = library_links(target)

        for path in links:
            self.assertEqual(
                Path(path).resolve(),
                Path(target.binary_path).resolve())

    @unittest.skipIf(not resolve('libm.so.6'), "No library to test with")
    def test_is_elf(self):
        self.assertFalse(is_elf('/proc/meminfo'))
        self.assertFalse(is_elf('/'))
        self.assertTrue(is_elf(resolve('libm.so.6')))
