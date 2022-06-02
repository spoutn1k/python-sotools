"""
Defines a derived class of set() with shared objects, along with a few methods,
to facilitate handling large amounts of libraries
"""

import re
import logging
from pathlib import Path

from sotools.util import flatten

from sotools.linker import resolve, LinkingError
from sotools.dl_cache import Flags

from elftools.common.exceptions import ELFError
from elftools.elf.elffile import ELFFile
from elftools.elf.dynamic import DynamicSection
from elftools.elf.gnuversions import (
    GNUVerDefSection,
    GNUVerNeedSection,
)


class Library:
    """
    Relevant ELF header fields used in the dynamic linking of libraries
    """

    @classmethod
    def from_path(cls, path):
        library = cls()

        with open(path, 'rb') as file:
            try:
                for section in ELFFile(file).iter_sections():
                    if isinstance(section, GNUVerDefSection):
                        library.__parse_ver_def(section)
                    elif isinstance(section, GNUVerNeedSection):
                        library.__parse_ver_need(section)
                    elif isinstance(section, DynamicSection):
                        library.__parse_dynamic(section)
                library.binary_path = getattr(file, 'name', file)
            except (ELFError, AttributeError) as err:
                logging.error("Error parsing '%s' for ELF data: %s",
                              getattr(file, 'name', file), err)

        return library

    def __init__(self):
        self.soname = ''
        self.dyn_dependencies = set()
        self.required_versions = {}
        self.defined_versions = set()

        self.rpath = []
        self.runpath = []
        self.binary_path = None

    def __parse_dynamic(self, section):

        def __fetch_tags(id_):
            return list(
                filter(lambda x: x.entry.d_tag == id_, section.iter_tags()))

        tags = __fetch_tags('DT_SONAME')
        if len(tags) == 1:
            self.soname = tags[0].soname

        tags = __fetch_tags('DT_RPATH')
        if len(tags) == 1:
            self.rpath = tags[0].rpath.split(':')

        tags = __fetch_tags('DT_RUNPATH')
        if len(tags) == 1:
            self.runpath = tags[0].runpath.split(':')

        tags = __fetch_tags('DT_NEEDED')
        self.dyn_dependencies = {tag.needed for tag in tags}

    def __parse_ver_def(self, section):
        self.defined_versions = {
            next(v_iter).name
            for _, v_iter in section.iter_versions()
        }

    def __parse_ver_need(self, section):
        needed = {}

        for ver, v_iter in section.iter_versions():
            needed[ver.name] = {ver.name for ver in v_iter}

        self.required_versions = needed

    def __hash__(self):
        """
        hash method tying the ELFData object to the soname, to use in sets
        """
        return hash(self.soname)

    def __eq__(self, other):
        if isinstance(other, Library):
            return self.soname == other.soname and self.defined_versions == other.defined_versions
        return NotImplemented

    def __gt__(self, rhs):
        if isinstance(rhs, Library):
            return self.soname > rhs.soname
        return NotImplemented

    def __repr__(self):
        return f"'{self.soname}' from '{self.binary_path}'"


class LibrarySet(set):
    """
    Set-like object to collect Libray objects
    """

    @classmethod
    def create_from(cls, library_list):
        """
        -> LibrarySet[Library]
        Given a list of str or pathlib.Path, create a cf.libraries.LibrarySet
        with all the libraries and their dependencies resolved.
        """

        def _process(element):
            path = None

            if isinstance(element, Path):
                path = element.as_posix()
            elif isinstance(element, str):
                if '/' in element:
                    path = Path(element).as_posix()
                else:
                    path = resolve(element,
                                   rpath=cache.rpath,
                                   runpath=cache.runpath)
            else:
                raise Exception(
                    f"Wrong type for LibrarySet.create_from: {type(element)}")

            if not path:
                raise LinkingError(element)

            return path

        cache = LibrarySet()

        for path in map(_process, library_list):
            cache.add(Library.from_path(path))

        return cache.resolve()

    def add(self, elem):
        """
        -> None
        Wraps the default set.add method

        If a element with a given hash is added to a set, python will avoid
        copying it over if the set already contains an element with the same
        hash. This is an issue when adding HostLibraries/GuestLibraries
        depicting the same library, as the hash needs to be their soname.

        This method gets rid of matching libraries before calling set.add
        """
        if not isinstance(elem, Library):
            raise Exception(
                f"Adding object of incompatible type {type(elem)} to LibrarySet !"
            )

        conflict = list(filter(lambda x: hash(x) == hash(elem), self))

        if len(conflict) == 1:
            self.discard(conflict.pop())

        super().add(elem)

    @property
    def rpath(self):
        """
        -> list(str)
        Return a set of the libraries rpaths merged together
        """
        return flatten(map(lambda x: x.rpath, self))

    @property
    def runpath(self):
        """
        -> list(str)
        Return a set of the libraries runpaths merged together
        """
        return flatten(map(lambda x: x.runpath, self))

    @property
    def defined_versions(self):
        return set(flatten(map(lambda x: x.defined_versions, self)))

    @property
    def required_versions(self):
        return set(
            flatten(flatten(map(lambda x: x.required_versions.values(),
                                self))))

    @property
    def top_level(self):
        """
        -> LibrarySet, subset of self
        Returns a set of all libraries included in self that are not depended
        upon from another library in the set
        """
        return LibrarySet(self - self.required_libraries)

    @property
    def linkers(self):
        """
        -> LibrarySet, subset of self
        Returns a set of all linkers present in the set.
        The linker is identified by its static-ness and definition of private GLIB symbols.
        """
        return LibrarySet(
            filter(lambda x: not x.dyn_dependencies and x in self.glib, self))

    @property
    def glib(self):
        """
        -> LibrarySet, subset of self
        Returns a set with all libraries tied to the available libc,
        recognizable by the GLIBC_PRIVATE symbols. Using these with any
        other libc will trigger a symbol error.
        """

        def references_private(lib):
            return 'GLIBC_PRIVATE' in flatten(lib.required_versions.values(
            )) or 'GLIBC_PRIVATE' in lib.defined_versions

        return LibrarySet(filter(references_private, self))

    @property
    def required_libraries(self):
        """
        -> LibrarySet, subset of self
        Returns a set of all libraries included in self that are depended
        upon from another library in the set
        """
        sonames = set(flatten(map(lambda x: x.dyn_dependencies, self)))
        return LibrarySet(filter(lambda x: x.soname in sonames, self))

    @property
    def sonames(self):
        """
        -> set(str)
        Returns a set with the sonames of all the libraries in self
        """
        return set(map(lambda x: x.soname, self))

    @property
    def missing_libraries(self):
        """
        -> set(str)
        Returns a set with the sonames of all the dependencies of the set's
        libraries not present in self
        """
        req_sonames = set(flatten(map(lambda x: x.dyn_dependencies, self)))
        return req_sonames - self.sonames

    @property
    def outdated_libraries(self):
        """
        -> LibrarySet, subset of self
        Sonames of libraries that do not implement all the symbols expected by
        the other libraries
        """
        outdated = LibrarySet()

        for library in self:
            for _soname, required in library.required_versions.items():
                matches = set()

                for obj in self:
                    if obj.soname == _soname:
                        matches.add(obj)

                if len(matches) != 1:
                    continue

                dependency = matches.pop()

                if required > dependency.defined_versions:
                    outdated.add(dependency)

        return outdated

    @property
    def complete(self):
        """
        -> bool
        Returns True if all the dependencies are resolved
        """
        return (len(self.missing_libraries) == 0
                and self.required_versions.issubset(self.defined_versions))

    def find(self, soname):
        """
        -> Library or None
        Returns the matching library if found in self, else None
        """
        query = re.escape(soname)
        matches = set(filter(lambda x: re.match(query, x.soname), self))

        return matches.pop() if matches else None

    def resolve(self, rpath=None, runpath=None):
        """
        -> LibrarySet, superset of self
        will try to resolve all dynamic depedencies of the set's members, then
        add them to the returned set

        if the returned set complete() method returns False, a library cannot
        be found by e4s-cl
        """
        superset = LibrarySet(self)
        arch_flags = None

        # Assert all libraries are from the same architecture and store the
        # appropriate flag in arch_flag
        # Calculate all flags and boil them down in a set, filtering out Nones
        search_flags = {Flags.expected_flags(lib.binary_path) for lib in self}
        valid_flags = set(filter(None, search_flags))
        if len(valid_flags) == 1:
            arch_flags = list(valid_flags)[0]
        else:
            logging.debug(
                "Resolving dependencies of a set with mixed architectures (%s) !",
                ",".join(valid_flags))

        missing = superset.missing_libraries
        change = True

        while change:
            for soname in missing:
                path = resolve(soname,
                               rpath=superset.rpath,
                               runpath=superset.runpath,
                               arch_flags=arch_flags)

                if not path:
                    continue

                superset.add(Library.from_path(path))

            change = superset.missing_libraries != missing
            missing = superset.missing_libraries

        return superset

    def ldd_format(self):
        """
        -> list(str)
        """

        def line(soname: str):
            lib = self.find(soname)
            if lib and lib.binary_path:
                return "\t%(soname)s => %(binary_path)s" % lib.__dict__
            return f"\t{soname} => not found"

        return list(map(line, set.union(self.sonames, self.missing_libraries)))
