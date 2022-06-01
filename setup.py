#!/usr/bin/env python

import importlib.util
from pathlib import Path
from setuptools import setup, find_packages

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
    "packages": find_packages(exclude=['tests']),
    "install_requires": DEPENDENCIES,
    "scripts": SCRIPTS,
}

setup(**install_options)
universal = 1
