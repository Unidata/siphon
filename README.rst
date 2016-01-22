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
    :alt: PyPI Package

.. image:: https://img.shields.io/pypi/dm/siphon.svg
    :target: https://pypi.python.org/pypi/siphon/
    :alt: PyPI Downloads

.. image:: https://binstar.org/unidata/siphon/badges/version.svg
    :target: https://binstar.org/unidata/siphon
    :alt: Binstar Package

.. image:: https://binstar.org/unidata/siphon/badges/downloads.svg
    :target: https://binstar.org/unidata/siphon
    :alt: Binstar Downloads

.. image:: https://travis-ci.org/Unidata/siphon.svg?branch=master
    :target: https://travis-ci.org/Unidata/siphon
    :alt: Travis Build Status

.. image:: https://codecov.io/github/Unidata/siphon/coverage.svg?branch=master
    :target: https://codecov.io/github/Unidata/siphon?branch=master
    :alt: Coveralls Coverage Status

.. image:: https://www.quantifiedcode.com/api/v1/project/e4c6ae8ad9d64a8a94f5454ff28615b1/badge.svg
    :target: https://www.quantifiedcode.com/app/project/e4c6ae8ad9d64a8a94f5454ff28615b1
    :alt: Code issues

.. image:: https://api.codacy.com/project/badge/grade/ebacd20b84ab4673bd6cd34f65c48af6
    :target: https://www.codacy.com/app/Unidata/siphon
    :alt: Codacy code issues

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

We support Python 2.7 as well as Python >= 3.3.

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

- requests>=1.2
- numpy>=1.8
- protobuf>=3.0.0a3

Developer Dependencies
----------------------

- pytest
- vcrpy
- flake8
