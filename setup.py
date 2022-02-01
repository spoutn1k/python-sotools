#!/usr/bin/env python

import os

try:
    # setuptools supports bdist_wheel
    from setuptools import setup
except ImportError:
    from distutils.core import setup

DEPENDENCIES = []

try:
    with open('requirements.txt') as fp:
        DEPENDENCIES = fp.read().split()
except FileNotFoundError:
    pass

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
    "version": '0.0.1',
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
