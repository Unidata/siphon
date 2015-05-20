from __future__ import print_function
from setuptools import setup, find_packages
import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'siphon/_version.py'
versioneer.versionfile_build = 'siphon/_version.py'
versioneer.tag_prefix = 'v'
versioneer.parentdir_prefix = 'siphon-'

ver = versioneer.get_version()
commands = versioneer.get_cmdclass()

setup(
    name = "siphon",
    version = ver,
    packages = find_packages(),
    cmdclass=commands,
    author = "Unidata Development Team",
    author_email = 'support-python@unidata.ucar.edu',
    license = 'MIT',
    url = "https://github.com/Unidata/siphon",
    test_suite = "nose.collector",
    description = ("A collection of Python utilities for interacting with the"
                                   "Unidata technology stack."),
    keywords='meteorology weather',
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Topic :: Scientific/Engineering',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'License :: OSI Approved :: MIT License'],

    install_requires=['numpy>=1.8', 'protobuf==3.0.0a1'],
    extras_require={
        'dev': ['ipython[all]>=3.1'],
        'doc': ['sphinx>=1.3', 'ipython[all]>=3.1'],
        'test': ['nosetest', 'vcrpy>=1.5']
    },

    download_url='https://github.com/Unidata/siphon/archive/v%s.tar.gz' % ver,)
