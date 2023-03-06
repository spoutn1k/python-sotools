"""
Library analysis and manipulation helpers
"""

from re import match
from os.path import realpath
from pathlib import Path
from typing import Set
from logging import debug

from sotools.libraryset import Library


def is_elf(path: Path) -> bool:
    """
    Returns a boolean if the file associated to the given path contains an ELF object.
    """
    try:
        with open(path, 'rb') as file:
            magic = file.read(4)

    except Exception:
        return False

    return magic == "\x7fELF".encode()


def library_links(shared_object: Library) -> Set[Path]:
    """
    This method resolves symbolic links that may exist and point to the
    library passed as an argument in the same directory as that library.

    Given the directory:
    lrwxrwxrwx. 1 root root   16 May 13  2019 libmpi.so -> libmpi.so.12.1.1
    lrwxrwxrwx. 1 root root   16 May 13  2019 libmpi.so.12 -> libmpi.so.12.1.1
    -rwxr-xr-x. 1 root root 2.7M May 13  2019 libmpi.so.12.1.1

    If any of those 3 files were to be passed as an argument, all would be
    returned.
    """
    if not isinstance(shared_object, Library):
        raise Exception(
            f"library_links: Wrong argument type: {type(shared_object)}")

    libname = Path(shared_object.binary_path).name

    # If no '.so' in the file name, return
    if not match(r'.*\.so.*', libname):
        debug("library_links: Error in format of %s", libname)
        return {Path(shared_object.binary_path)}

    cleared = set()
    prefix = libname.split('.so')[0]
    library_file = realpath(shared_object.binary_path)

    def _glob_links(prefix_):
        for file in list(Path(library_file).parent.glob(f"{prefix_}.so*")):
            if realpath(file) == library_file:
                cleared.add(file)

    _glob_links(prefix)

    # glib files are named as libc-2.33.so, but the links are named libc.so.x
    matches = match(r'(?P<prefix>lib[a-z_]+)-.+', prefix)
    if matches:
        _glob_links(matches.group('prefix'))

    # If we encounter a special case of symlink presenting as another library,
    # return the symlink and the shared object being pointed to.
    if shared_object.soname != libname:
        cleared.add(Path(shared_object.binary_path))
        cleared.add(Path(library_file))

    return cleared
