# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Setup script for installing Siphon."""

from __future__ import print_function

import sys

from setuptools import find_packages, setup
import versioneer


ver = versioneer.get_version()

# Need to conditionally add enum support for older Python
dependencies = ['numpy>=1.8', 'protobuf>=3.0.0a3', 'requests>=1.2', 'beautifulsoup4>=4.6',
                'pandas']
if sys.version_info < (3, 4):
    dependencies.append('enum34')

setup(
    name='siphon',
    version=ver,
    packages=find_packages(),
    author='Unidata Development Team',
    author_email='support-python@unidata.ucar.edu',
    license='BSD 3-Clause',
    url='https://github.com/Unidata/siphon',
    description=('A collection of Python utilities for interacting with the '
                 'Unidata technology stack.'),
    keywords='meteorology weather',
    classifiers=['Development Status :: 3 - Alpha',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Topic :: Scientific/Engineering',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'License :: OSI Approved :: BSD License'],

    install_requires=dependencies,
    extras_require={
        'netcdf': 'netCDF4>=1.1.0',
        'dev': 'ipython[all]>=3.1',
        'test': ['pytest', 'pytest-flake8', 'pytest-runner',
                 'netCDF4>=1.1.0',
                 'flake8>3.2.0', 'flake8-builtins', 'flake8-comprehensions',
                 'flake8-copyright', 'flake8-docstrings', 'flake8-import-order',
                 'flake8-mutable', 'flake8-pep3101', 'flake8-print', 'flake8-quotes',
                 'pep8-naming',
                 'vcrpy~=1.5,!=1.7.0,!=1.7.1,!=1.7.2,!=1.7.3', 'xarray>=0.10.2'],
        'doc': ['sphinx>=1.3,!=1.6.4', 'sphinx-gallery', 'doc8', 'recommonmark'],
        # SciPy needed for cartopy; we don't use cartopy[plotting] because
        # that will pull in GDAL.
        'examples': ['matplotlib>=1.3', 'cartopy>=0.13.1', 'scipy', 'metpy']
    },

    download_url='https://github.com/Unidata/siphon/archive/v{}.tar.gz'.format(ver),
    cmdclass=versioneer.get_cmdclass(),
)
