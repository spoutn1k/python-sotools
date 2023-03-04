from copy import deepcopy
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

    executable = LibrarySet([Library.from_path(path)])
    libraries = deepcopy(executable)

    return LibrarySet(libraries.resolve() - executable)
