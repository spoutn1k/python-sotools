# python-sotools

Collection of tools to debug and diagnose ELF objects dynamic linking.

## Dynamic linker

The module contains methods to mimic the default dynamic linker on Linux. The [`resolve`](https://github.com/spoutn1k/python-sotools/blob/ba7a3bdda288f4edd50133e826144224cc2bf561/sotools/linker.py#L31) method implements all the rules involving the search and selection of a shared object given a shared object name (soname) string.

### Dynamic linker cache

The dynamic linker cache (usually present at `/etc/ld.so.cache`) is a database generated at install time to cache the locations of select shared objects on the system. `python-sotools` supports reading and parsing this file, along with customized search for matches.

### Library set

To simplify the use of the linker, the `LibrarySet` object is a specialization of a python `set` that allows to quickly resolve a dependency tree. It contains `Library` objects and is complete when all dependencies are contained in the set, and allows to verify all the members' required definitions are also present in another set member.

## Scripts

The following scripts are installed automatically when installing `python-sotools`:

### `ldd.py`

Simple re-implementation of ldd with the contents of `python-sotools`. This version does not use the actual linker and can be trusted not to run any code when executed with unknown executables, unlike the original.

### `sowhich`

Which library is resolved ? This command returns the path for the library name given as an argument. That's it.
