=================
Developer's Guide
=================

------------
Requirements
------------

- pytest
- flake8
- sphinx >= 1.3
- sphinx-rtd-theme >= 0.1.7
- IPython >= 3.1
- pandoc (not a python package)

~~~~~
Conda
~~~~~

Settings up a development environment in Siphon is as easy as (from the
base of the repository):

.. parsed-literal::
    conda env create
    conda develop -n devel .

The ``environment.yml`` contains all of the configuration needed to easily
set up the environment, called ``devel``. The second line sets up conda to
run directly out of the git repository.

--------------
Making Changes
--------------

The changes to the Siphon source (and documentation) should be made via GitHub pull requests
against ``main``, even for those with administration rights. While it's tempting to make
changes directly to ``main`` and push them up, it is better to make a pull request so that
others can give feedback. If nothing else, this gives a chance for the automated tests to run
on the PR. This can eliminate "brown paper bag" moments with buggy commits on the main branch.

During the Pull Request process, before the final merge, it's a good idea to rebase the branch
and squash together smaller commits. It's not necessary to flatten the entire branch, but it
can be nice to eliminate small fixes and get the merge down to logically arranged commit. This
can also be used to hide sins from history--this is the only chance, since once it hits
``main``, it's there forever!

----------
Versioning
----------

To manage identifying the version of the code, Siphon relies upon ``setuptools_scm``.
It takes the current version of
the source from git tags and any additional commits. For development, the version will have a
string like ``0.1.1+76.g136e37b.dirty``, which comes from ``git describe``. This version means
that the current code is 76 commits past the 0.1.1 tag, on git hash ``136e37b``, with local
changes on top (indicated by ``dirty``). For a release, or non-git repo source dir, the version
will just come from the most recent tag (i.e. ``v0.1.1``).

To make a new version, simply add a new tag with a name like ``vMajor.Minor.Bugfix`` and push
to GitHub. Github will add a new release with a source archive.zip file.

-------
Testing
-------

Unit tests are the lifeblood of the project, as it ensures that we can continue to add and
change the code and stay confident that things have not broken. Running the tests requires
``pytest``, which is easily available through ``conda`` or ``pip``. Running the tests can be
done by:

.. parsed-literal::
    pytest tests

This gives you the option of passing a path to the directory with tests to
run, which can speed running only the tests of interest when doing development. For instance,
to only run the tests in the ``siphon/cdmr`` directory, use:

.. parsed-literal::
    pytest siphon/cdmr

----------
Code Style
----------

Siphon uses the Python code style outlined in `PEP8
<https://peps.python.org/pep-0008/>`_. For better or worse, this is what the majority
of the Python world uses. The one deviation is that line length limit is 95 characters. 80 is a
good target, but some times longer lines are needed.

While the authors are no fans of blind adherence to style and so-called project "clean-ups"
that go through and correct code style, Siphon has adopted this style from the outset.
Therefore, it makes sense to enforce this style as code is added to keep everything clean and
uniform. To this end, part of the automated testing for Siphon checks style. To check style
locally within the source directory you can use the ``flake8`` tool. Running it from the root
of the source directory is as easy as:

.. parsed-literal::
    flake8 siphon

-------------
Documentation
-------------

Siphon's documentation is built using sphinx >= 1.4. API documentation is automatically
generated from docstrings, written using the
`NumPy docstring standard <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_.
There are also examples in the ``examples/`` directory.

The documentation is hosted on `GitHub Pages <https://unidata.github.io/siphon>`_. The docs are
built automatically from ``main`` with every build on GitHub Actions; every merged PR will
have the built docs upload to GitHub Pages. As part of the build, the documentation is also
checked with ``doc8``. To see what the docs will look like, you also need to install the
``sphinx-rtd-theme`` package.

-----------
Other Tools
-----------

Continuous integration is performed by
`GitHub Actions <https://github.com/Unidata/siphon/actions>`_.
This integration runs the unit tests on Linux for all supported versions of Python, as well
as runs against the minimum package versions, using PyPI packages. This also runs against
a (non-exhaustive) matrix of python versions on macOS and Windows. In addition to these tests,
GitHub actions also builds the documentation and runs the examples across multiple platforms
and Python versions, as well as checks for any broken web links. ``flake8`` (along with a
variety of plugins found in ``ci/linting.txt``) and ``ruff`` are also run against the code to
check formatting using another job on GitHub Actions. As part of this linting job, the docs
are also checked using the ``doc8`` tool, and spelling is checked using ``codespell``.
Configurations for these are in a variety of files in ``.github/workflows``.

Test coverage is monitored by `codecov.io <https://codecov.io/github/Unidata/siphon>`_.

---------
Releasing
---------

To create a new release:

1. Go to the GitHub page and make a new release. The tag should be a sensible version number,
   like v1.0.0. Add a name (can just be the version) and add some notes on what the big
   changes are.
2. Do a pull locally to grab the new tag. This will ensure that ``setuptools_scm`` will give
   you the proper version.
3. (optional) Perform a ``git clean -f -x -d`` from the root of the repository. This will
   **delete** everything not tracked by git, but will also ensure clean source distribution.
   ``MANIFEST.in`` is set to include/exclude mostly correctly, but could miss some things.
4. Run ``python -m build`` (this requires that ``build`` is installed).
5. Upload using ``twine``: ``twine upload dist/*``, assuming the ``dist/`` directory contains
   only files for this release. This upload process will include any changes to the ``README``
   as well as any updated flags from ``pyproject.toml``.
