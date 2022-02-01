from pathlib import Path
from sotools import is_elf
from sotools.libraryset import Library, LibrarySet


class NotELFError(Exception):
    pass


def ldd(binary: str):
    """
    -> LibrarySet
    """

    path = Path(binary)

    if not is_elf(path):
        raise NotELFError

    libs = LibrarySet()

    with open(path, 'rb') as binary:
        libs.add(Library(binary))

    return libs.resolve()
