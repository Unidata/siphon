==================
Installation Guide
==================

------------
Requirements
------------
In general, Siphon tries to support minor versions of dependencies released within the last two
years. For Python itself, that means supporting the last two minor releases.

Siphon currently supports the following versions of required dependencies:
  - requests >= 1.2
  - numpy >= 1.8.0
  - protobuf >= 3.0.0
  - beautifulsoup4>=4.6
  - pandas

Installation Instructions for NumPy can be found at:
  https://numpy.org/install/

------------
Installation
------------

The easiest way to install Siphon is through ``pip``:

.. parsed-literal::
    pip install siphon

Siphon can also be installed through ``conda``:

.. parsed-literal::
    conda install -c unidata siphon

Additionally, Siphon can be installed with ``conda-forge``:

.. parsed-literal::
    conda install -c conda-forge siphon

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
