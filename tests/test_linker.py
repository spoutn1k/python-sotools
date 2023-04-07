import os
import unittest
from pathlib import Path
from sotools.linker import (
    resolve,
    _search_paths,
    _linker_path,
)

from tests import ASSETS


class LinkerTest(unittest.TestCase):

    def test_search_paths(self):
        found = _search_paths(
            "libmakebelieve.so.0",
            [Path("/usr/lib")],
        )
        self.assertIsNone(found)

        found = _search_paths(
            "libmakebelieve.so.0",
            [Path("/usr/lib"), ASSETS],
        )
        self.assertIsNotNone(found)

    def test_resolve(self):
        found = resolve("libmakebelieve.so.0")
        self.assertIsNone(found)

        found = resolve("libc.so.6")
        self.assertIsNotNone(found)

    def test_resolve_ld_path(self):
        _linker_path.cache_clear()
        orig_path = os.environ.get("LD_LIBRARY_PATH")
        os.environ["LD_LIBRARY_PATH"] = ASSETS.as_posix()

        found = resolve("libmakebelieve.so.0")
        self.assertIsNotNone(found)

        if orig_path:
            os.environ["LD_LIBRARY_PATH"] = orig_path

    def test_resolve_rpath(self):
        found = resolve("libmakebelieve.so.0", rpath=[ASSETS.as_posix()])
        self.assertIsNotNone(found)

    def test_resolve_runpath(self):
        found = resolve("libmakebelieve.so.0", runpath=[ASSETS.as_posix()])
        self.assertIsNotNone(found)

    def test_resolve_absolute(self):
        regular = resolve("libmakebelieve.so.0", runpath=[ASSETS.as_posix()])
        self.assertEqual(regular, ASSETS / "libmakebelieve.so.0")

        absolute = resolve("libmakebelieve.so.0",
                           runpath=[ASSETS.as_posix()],
                           absolute=True)
        self.assertEqual(absolute, ASSETS / "libmakebelieve.so.0.0.1")
