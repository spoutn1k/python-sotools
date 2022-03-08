#!/usr/bin/env python

from pathlib import Path
import importlib.util

try:
    # setuptools supports bdist_wheel
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Load metadata from the package's version module
spec = importlib.util.spec_from_file_location('version',
                                              Path('sotools', 'version.py'))
metadata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metadata)

DEPENDENCIES = ['pyelftools']

VERSION = metadata.__version__

MODULES = {"sotools": "sotools"}

SCRIPTS = ["sowhich.py", "ldd.py"]

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 2 - Pre-Alpha',
    'Environment :: Console',
    'Operating System :: POSIX :: Linux',
    'Natural Language :: English',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

install_options = {
    "name": 'python-sotools',
    "version": VERSION,
    "author": "Jean-Baptiste Skutnik",
    "description": "python implementation of ld.so rules",
    "long_description": "python implementation of ld.so rules",
    "classifiers": CLASSIFIERS,
    "packages": MODULES,
    "package_dir": MODULES,
    "install_requires": DEPENDENCIES,
    "scripts": SCRIPTS,
}

setup(**install_options)
universal = 1
