==================
Installation Guide
==================

------------
Requirements
------------
In general, Siphon tries to support minor versions of dependencies released within the last two
years. For Python itself, that means supporting the last two minor releases.

Siphon currently supports the following versions of required dependencies:

.. literalinclude:: ../pyproject.toml
   :start-at: beautifulsoup4
   :end-at: requests

Installation Instructions for NumPy can be found at:
  https://numpy.org/install/

------------
Installation
------------

The easiest way to install Siphon is through ``pip``:

.. parsed-literal::
    pip install siphon

Siphon can also be installed through ``conda``, using the ``conda-forge`` channel:

.. parsed-literal::
    conda install -c conda-forge siphon

The source code can also be grabbed from `GitHub <https://github.com/Unidata/siphon>`_. From
the base of the source directory, run:

.. parsed-literal::
    pip install .

This will build and install Siphon into your current Python installation.


--------
Examples
--------

The Siphon source comes with a set of examples in the ``examples/`` directory.

These examples are also seen within the documentation in the :ref:`examples-index`.
