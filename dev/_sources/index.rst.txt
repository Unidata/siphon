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
data hosted on a `THREDDS Data Server`__.

__ https://www.unidata.ucar.edu/software/thredds/current/tds/

Siphon is still in an early stage of development, and as such
**no APIs are considered stable.** While we won't break things
just for fun, many things may still change as we work through
design issues.

We support Python 2.7 as well as Python >= 3.4.

----------
Contact Us
----------

* For questions and discussion about Siphon, join Unidata's python-users_
  mailing list
* The source code is available on GitHub_
* Bug reports and feature requests should be directed to the
  `GitHub issue tracker`__
* Siphon has a Gitter_ chatroom for more "live" communication
* If you use Siphon in a publication, please see :ref:`Citing_Siphon`.

.. _python-users: https://www.unidata.ucar.edu/support/#mailinglists
.. _GitHub: https://github.com/Unidata/siphon
.. _Gitter: https://gitter.im/Unidata/siphon
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
