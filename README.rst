Siphon
======

.. image:: https://img.shields.io/pypi/l/siphon.svg
    :target: https://pypi.python.org/pypi/siphon/
    :alt: License

.. image:: https://img.shields.io/github/issues/Unidata/siphon.svg
    :target: http://www.github.com/Unidata/siphon/issues
    :alt: GitHub Issues

.. image:: https://img.shields.io/github/tag/Unidata/siphon.svg
    :target: https://github.com/Unidata/siphon/tags
    :alt: GitHub Tags

.. image:: https://img.shields.io/pypi/v/siphon.svg
    :target: https://pypi.python.org/pypi/siphon/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/siphon.svg
    :target: https://pypi.python.org/pypi/siphon/
    :alt: Downloads

.. image:: https://travis-ci.org/Unidata/siphon.svg?branch=master
    :target: https://travis-ci.org/Unidata/siphon
    :alt: Travis Build Status

.. image:: https://coveralls.io/repos/Unidata/siphon/badge.svg?branch=master
    :target: https://coveralls.io/r/Unidata/siphon
    :alt: Coveralls Coverage Status

.. image:: https://landscape.io/github/Unidata/siphon/master/landscape.svg?style=flat
    :target: https://landscape.io/github/Unidata/siphon/master
    :alt: Code Health

.. image:: https://readthedocs.org/projects/pip/badge/?version=latest
    :target: http://siphon.readthedocs.org/en/latest/
    :alt: Latest Doc Build Status

.. image:: https://readthedocs.org/projects/pip/badge/?version=stable
    :target: http://siphon.readthedocs.org/en/stable/
    :alt: Stable Doc Build Status

Siphon is a collection of Python utilities for downloading data from Unidata
data technologies.

Siphon is still in an early stage of development, and as such
**no APIs are considered stable.** While we won't break things
just for fun, many things may still change as we work through
design issues.

We support Python 2.7 as well as Python >= 3.2.

Installation
------------
::

    git clone https://github.com/Unidata/siphon.git
    cd siphon
    python setup.py install

Important Links
---------------

- Source code repository: https://github.com/Unidata/siphon
- HTML Documentation (stable release): http://siphon.readthedocs.org/en/stable/
- HTML Documentation (development): http://siphon.readthedocs.org/en/latest/
- Issue tracker: http://github.com/Unidata/siphon/issues

Dependencies
------------

- numpy>=1.8
- protobuf>=3.0.0a3

Developer Dependencies
----------------------

- nose
- vcrpy
- flake8
