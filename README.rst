Siphon
======

|License| |PRWelcome|

|Docs| |PyPI| |Conda|

|Travis| |AppVeyor| |CodeCov|

|Codacy|


.. |License| image:: https://img.shields.io/pypi/l/siphon.svg
    :target: https://pypi.python.org/pypi/siphon/
    :alt: License

.. |PyPI| image:: https://img.shields.io/pypi/v/siphon.svg
    :target: https://pypi.python.org/pypi/siphon/
    :alt: PyPI Package

.. |Conda| image:: https://anaconda.org/conda-forge/siphon/badges/version.svg
    :target: https://anaconda.org/conda-forge/siphon
    :alt: Conda Package

.. |Travis| image:: https://travis-ci.org/Unidata/siphon.svg?branch=master
    :target: https://travis-ci.org/Unidata/siphon
    :alt: Travis Build Status

.. |AppVeyor| image:: https://ci.appveyor.com/api/projects/status/stxqunhdyqu75u3r/branch/master?svg=true
    :target: https://ci.appveyor.com/project/Unidata/siphon/branch/master
    :alt: AppVeyor Build Status

.. |CodeCov| image:: https://codecov.io/github/Unidata/siphon/coverage.svg?branch=master
    :target: https://codecov.io/github/Unidata/siphon?branch=master
    :alt: Code Coverage Status

.. |Codacy| image:: https://api.codacy.com/project/badge/grade/ebacd20b84ab4673bd6cd34f65c48af6
    :target: https://www.codacy.com/app/Unidata/siphon
    :alt: Codacy code issues

.. |Docs| image:: https://img.shields.io/badge/docs-stable-brightgreen.svg
    :target: http://unidata.github.io/siphon
    :alt: Latest Docs

.. |PRWelcome| image:: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=round-square
    :target: https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github
    :alt: PRs Welcome

Siphon is a collection of Python utilities for downloading data from Unidata
data technologies. See our `support page`__ for ways to get help with Siphon.

__ https://github.com/Unidata/siphon/blob/master/SUPPORT.md

Siphon is still in an early stage of development, and as such
**no APIs are considered stable.** While we won't break things
just for fun, many things may still change as we work through
design issues.

We support Python 2.7 as well as Python >= 3.4.

Installation
------------
::

    git clone https://github.com/Unidata/siphon.git
    cd siphon
    python setup.py install

Important Links
---------------

- Source code repository: https://github.com/Unidata/siphon
- HTML Documentation: http://unidata.github.io/siphon/
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
