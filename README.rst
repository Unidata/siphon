Siphon
======

|License| |PRWelcome|

|Docs| |PyPI| |Conda|

|CodeCov|

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

.. |CodeCov| image:: https://codecov.io/github/Unidata/siphon/coverage.svg?branch=main
    :target: https://codecov.io/github/Unidata/siphon?branch=main
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

__ https://github.com/Unidata/siphon/blob/main/SUPPORT.md

Siphon follows `semantic versioning <https://semver.org>`_ in its version number. With our
current 0.x version, that implies that Siphon's APIs (application programming interfaces) are
still evolving (we won't break things just for fun, but many things are still changing as we
work through design issues). Also, for a version `0.x.y`, we change `x` when we
release new features, and `y` when we make a release with only bug fixes.

We support Python >= 3.7.

Important Links
---------------

- Source code repository: https://github.com/Unidata/siphon
- HTML Documentation: http://unidata.github.io/siphon/
- Unidata Python Gallery: https://unidata.github.io/python-gallery/
- Issue tracker: http://github.com/Unidata/siphon/issues
- "python-siphon" tagged questions on Stack Overflow: https://stackoverflow.com/questions/tagged/python-siphon
- Gitter chat room: https://gitter.im/Unidata/siphon

Dependencies
------------

- requests>=1.2
- numpy>=1.8
- protobuf>=3.0.0a3
- beautifulsoup4>=4.6
- pandas

Developer Dependencies
----------------------

- pytest
- vcrpy
- flake8
