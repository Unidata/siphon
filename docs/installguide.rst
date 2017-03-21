==================
Installation Guide
==================

------------
Requirements
------------
Siphon supports Python 2.7 as well as Python >= 3.4. Python 3.6 is the recommended version.

Siphon requires the following packages:
  - requests >= 1.2
  - numpy >= 1.8.0
  - protobuf >= 3.0.0

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
