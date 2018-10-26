.. toctree::
  :maxdepth: 1
  :hidden:

  installguide
  api/index
  examples/index
  developerguide
  CONTRIBUTING
  citing

======
Siphon
======

Siphon is a collection of Python utilities for downloading data from remote
data services. Much of Siphon's current functionality focuses on access to
data hosted on a `THREDDS Data Server`__. It also provides clients to a variety
of simple web services.

__ https://www.unidata.ucar.edu/software/thredds/current/tds/

Siphon follows `semantic versioning <https://semver.org>`_ in its version number. With our
current 0.x version, that implies that Siphon's APIs (application programming interfaces) are
still evolving (we won't break things just for fun, but many things are still changing as we
work through design issues). Also, for a version `0.x.y`, we change `x` when we
release new features, and `y` when we make a release with only bug fixes.

We support Python >= 3.5 and currently support Python 2.7.

.. warning::
  We are dropping support for Python 2.7 in the Fall of 2019. For more details and rationale
  behind this decision, see :ref:`python27`.

----------
Contact Us
----------

* For questions about Siphon, please ask them using the "python-siphon" tag on StackOverflow_.
  Our developers are actively monitoring for questions there.
* You can also email `Unidata's
  python support email address <mailto: support-python@unidata.ucar.edu>`_
* The source code is available on GitHub_
* Bug reports and feature requests should be directed to the
  `GitHub issue tracker`__
* Siphon has a Gitter_ chatroom for more "live" communication
* If you use Siphon in a publication, please see :ref:`Citing_Siphon`.
* For release announcements, join Unidata's python-users_ mailing list

.. _python-users: https://www.unidata.ucar.edu/support/#mailinglists
.. _GitHub: https://github.com/Unidata/siphon
.. _Gitter: https://gitter.im/Unidata/siphon
.. _StackOverflow: https://stackoverflow.com/questions/tagged/python-siphon
__ https://github.com/Unidata/siphon/issues

---------------
Other Resources
---------------

* Unidata's Python gallery_ contains many examples using Siphon to access remote data
* The materials_ for Unidata's annual Python training workshop includes some tutorials on
  using Siphon.

.. _gallery: https://unidata.github.io/python-gallery
.. _materials: https://unidata.github.io/unidata-python-workshop

-------
License
-------

Siphon is available under the terms of the open source `BSD 3-Clause license`__.

__ https://raw.githubusercontent.com/Unidata/siphon/master/LICENSE

----------------
Related Projects
----------------

* netCDF4-python_ is the officially blessed Python API for netCDF_
* metpy_ is toolkit for using Python in meteorology applications

.. _netCDF4-python: https://unidata.github.io/netcdf4-python/
.. _netCDF: https://www.unidata.ucar.edu/software/netcdf/
.. _metpy: https://unidata.github.io/MetPy/
