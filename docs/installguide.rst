==================
Installation Guide
==================

.. _python27:

------------------
Python 2.7 Support
------------------
In the Fall 2019, we will be dropping support for Python 2.7. This follows movement from
other packages within the `scientific Python ecosystem <http://python3statement.org/>`_.
This includes:

* Core Python developers will
  `stop support for Python 2.7 January 1, 2020 <https://pythonclock.org/>`_
* NumPy feature releases will be
  `Python 3 only starting January 1, 2019 <https://docs.scipy.org/doc/numpy/neps/dropping-python2.7-proposal.html>`_,
  and support for the last release supporting Python 2 will end January 1, 2020.
* XArray will drop
  `2.7 January 1, 2019 as well <https://github.com/pydata/xarray/issues/1830>`_
* Matplotlib's 3.0 release, tentatively Summer 2018,
  `will be Python 3 only <https://mail.python.org/pipermail/matplotlib-devel/2017-October/000892.html>`_;
  the current 2.2 release will be the last long term release that supports 2.7, and its support
  will cease January 1, 2020.

The last release of Siphon before this time (Spring or Summer 2019) will be the last that
support Python 2.7. This version of Siphon will **not** receive any long term support or
additional bug fix releases after the next minor release. The packages for this version *will*
remain available on Conda or PyPI.

------------
Requirements
------------
In general, Siphon tries to support minor versions of dependencies released within the last two
years. For Python itself, that means supporting the last two minor releases, as well as
currently supporting Python 2.7.

Siphon currently supports the following versions of required dependencies:
  - requests >= 1.2
  - numpy >= 1.8.0
  - protobuf >= 3.0.0
  - beautifulsoup4>=4.6
  - pandas

Installation Instructions for NumPy can be found at:
  https://www.scipy.org/scipylib/download.html

------------
Installation
------------

The easiest way to install Siphon is through ``pip``:

.. parsed-literal::
    pip install siphon

The source code can also be grabbed from `GitHub <https://github.com/Unidata/siphon>`_. From
the base of the source directory, run:

.. parsed-literal::
    python setup.py install

This will build and install Siphon into your current Python installation.

--------
Examples
--------

The Siphon source comes with a set of examples in the ``examples/`` directory.

These examples are also seen within the documentation in the :ref:`examples-index`.
