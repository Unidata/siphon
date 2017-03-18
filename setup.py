from __future__ import print_function
import sys
from setuptools import setup, find_packages
import versioneer


ver = versioneer.get_version()

# Need to conditionally add enum support for older Python
dependencies = ['numpy>=1.8', 'protobuf>=3.0.0a3', 'requests>=1.2']
if sys.version_info < (3, 4):
    dependencies.append('enum34')

setup(
    name="siphon",
    version=ver,
    packages=find_packages(),
    author="Unidata Development Team",
    author_email='support-python@unidata.ucar.edu',
    license='MIT',
    url="https://github.com/Unidata/siphon",
    description=("A collection of Python utilities for interacting with the "
                 "Unidata technology stack."),
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
                 'License :: OSI Approved :: MIT License'],

    install_requires=dependencies,
    extras_require={
        'netcdf': 'netCDF4>=1.1.0',
        'dev': 'ipython[all]>=3.1',
        'test': ['pytest', 'pytest-runner', 'netCDF4>=1.1.0',
                 'vcrpy~=1.5,!=1.7.0,!=1.7.1,!=1.7.2,!=1.7.3', 'xarray>=0.6'],
        'doc': ['sphinx>=1.3', 'nbconvert>=4.0', 'IPython>=4.0'],
        'examples': ['matplotlib>=1.3', 'cartopy>=0.13.1', 'scipy']
    },

    download_url='https://github.com/Unidata/siphon/archive/v%s.tar.gz' % ver,)
