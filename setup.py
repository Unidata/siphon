import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "pyudl",
    version = "0.1",
    packages = find_packages(),
    author = "Unidata Development Team",
    license = read('LICENSE'),
    url = "https://github.com/Unidata/pyudl",
    test_suite = "nose.collector",
    description = ("A collection of Python utilities for interacting with the"
                                   "Unidata technology stack."),
    long_description = read('README.md'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python"
    ]
)
