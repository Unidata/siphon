==================
Installation Guide
==================

------------
Requirements
------------
Siphon supports Python 2.7 as well as Python >= 3.2. Python 3.4 is the recommended version.

Siphon requires the following packages:
  - NumPy >= 1.8.0
  - protobuf == 3.0.0a1

Installation Instructions for NumPy can be found at:
  http://www.scipy.org/scipylib/download.html

------------
Installation
------------

The easiest way to install Siphon is through ``pip``:

.. parsed-literal::
    pip install siphon

The source code can also be grabbed from `GitHub <http://github.com/Unidata/siphon>`_. From
the base of the source directory, run:

.. parsed-literal::
    python setup.py install

This will build and install Siphon into your current Python installation.

--------
Examples
--------

The Siphon source comes with a set of example IPython notebooks in the ``examples/notebooks`` directory.
These can also be converted to standalone scripts (provided IPython is installed) using:

.. parsed-literal::
    python setup.py examples

These examples are also seen within the documentation in the :ref:`examples-index`.
