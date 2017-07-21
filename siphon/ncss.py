# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Support making data requests to the NetCDF subset service (NCSS) on a TDS.

This includes forming proper queries as well as parsing the returned data.
"""

import atexit
from io import BytesIO
from os import remove
import platform
import xml.etree.ElementTree as ET

import numpy as np

from .http_util import DataQuery, HTTPEndPoint, parse_iso_date
from .ncss_dataset import NCSSDataset


def default_unit_handler(data, units=None):  # pylint:disable=unused-argument
    """Handle units in the default manner.

    Ignores units and just returns :func:`numpy.array`.
    """
    return np.array(data)


class NCSS(HTTPEndPoint):
    """Wrap access to the NetCDF Subset Service (NCSS) on a THREDDS server.

    Simplifies access via HTTP to the NCSS endpoint. Parses the metadata, provides
    data download and parsing based on the appropriate query.

    Attributes
    ----------
    metadata : NCSSDataset
        Contains the result of parsing the NCSS endpoint's dataset.xml. This has
        information about the time and space coverage, as well as full information
        about all of the variables.
    variables : set(str)
        Names of all variables available in this dataset
    unit_handler : callable
        Function to handle units that come with CSV/XML data. Should be a callable that
        takes a list of string values and unit str (can be :data:`None`), and returns the
        desired representation of values. Defaults to ignoring units and returning
        :func:`numpy.array`.

    """

    # Need staticmethod to keep this from becoming a bound method, where self
    # is passed implicitly
    unit_handler = staticmethod(default_unit_handler)

    def _get_metadata(self):
        # Need to use .content here to avoid decode problems
        meta_xml = self.get_path('dataset.xml').content
        root = ET.fromstring(meta_xml)
        self.metadata = NCSSDataset(root)
        self.variables = set(self.metadata.variables.keys())

    def query(self):
        """Return a new query for NCSS.

        Returns
        -------
        query : NCSSQuery
            The newly created query

        """
        return NCSSQuery()

    def validate_query(self, query):
        """Validate a query.

        Determines whether `query` is well-formed. This includes checking for all
        required parameters, as well as checking parameters for valid values.

        Parameters
        ----------
        query : NCSSQuery
            The query to validate

        Returns
        -------
        valid : bool
            Whether `query` is valid.

        """
        # Make sure all variables are in the dataset
        return bool(query.var) and all(var in self.variables for var in query.var)

    def get_data(self, query):
        """Fetch parsed data from a THREDDS server using NCSS.

        Requests data from the NCSS endpoint given the parameters in `query` and
        handles parsing of the returned content based on the mimetype.

        Parameters
        ----------
        query : NCSSQuery
            The parameters to send to the NCSS endpoint

        Returns
        -------
        Parsed data response from the server. Exact format depends on the format of the
        response.

        See Also
        --------
        get_data_raw

        """
        resp = self.get_query(query)
        return response_handlers(resp, self.unit_handler)

    def get_data_raw(self, query):
        """Fetch raw data from a THREDDS server using NCSS.

        Requests data from the NCSS endpoint given the parameters in `query` and
        returns the raw bytes of the response.

        Parameters
        ----------
        query : NCSSQuery
            The parameters to send to the NCSS endpoint

        Returns
        -------
        content : bytes
            The raw, un-parsed, data returned by the server

        See Also
        --------
        get_data

        """
        return self.get_query(query).content


class NCSSQuery(DataQuery):
    """Represent a query to the NetCDF Subset Service (NCSS).

    Expands on the queries supported by :class:`~siphon.http_util.DataQuery` to add queries
    specific to NCSS.
    """

    def projection_box(self, min_x, min_y, max_x, max_y):
        """Add a bounding box in projected (native) coordinates to the query.

        This adds a request for a spatial bounding box, bounded by (`min_x`, `max_x`) for
        x direction and (`min_y`, `max_y`) for the y direction. This modifies the query
        in-place, but returns ``self`` so that multiple queries can be chained together
        on one line.

        This replaces any existing spatial queries that have been set.

        Parameters
        ----------
        min_x : float
            The left edge of the bounding box
        min_y : float
            The bottom edge of the bounding box
        max_x : float
            The right edge of the bounding box
        max_y: float
            The top edge of the bounding box

        Returns
        -------
        self : NCSSQuery
            Returns self for chaining calls

        """
        self._set_query(self.spatial_query, minx=min_x, miny=min_y,
                        maxx=max_x, maxy=max_y)
        return self

    def accept(self, fmt):
        """Set format for data returned from NCSS.

        This modifies the query in-place, but returns `self` so that multiple queries
        can be chained together on one line.

        Parameters
        ----------
        fmt : str
            The format to send to the server.

        Returns
        -------
        self : NCSSQuery
            Returns self for chaining calls

        """
        return self.add_query_parameter(accept=fmt)

    def add_lonlat(self, value=True):
        """Set whether NCSS should add latitude/longitude to returned data.

        This is only used on grid requests. Used to make returned data CF-compliant.
        This modifies the query in-place, but returns `self` so that multiple queries
        can be chained together on one line.

        Parameters
        ----------
        value : bool, optional
            Whether to add latitude/longitude information. Defaults to True.

        Returns
        -------
        self : NCSSQuery
            Returns self for chaining calls

        """
        return self.add_query_parameter(addLatLon=value)

    def strides(self, time=None, spatial=None):
        """Set time and/or spatial (horizontal) strides.

        This is only used on grid requests. Used to skip points in the returned data.
        This modifies the query in-place, but returns `self` so that multiple queries
        can be chained together on one line.

        Parameters
        ----------
        time : int, optional
            Stride for times returned. Defaults to None, which is equivalent to 1.
        spatial : int, optional
            Stride for horizontal grid. Defaults to None, which is equivalent to 1.

        Returns
        -------
        self : NCSSQuery
            Returns self for chaining calls

        """
        if time:
            self.add_query_parameter(timeStride=time)
        if spatial:
            self.add_query_parameter(horizStride=spatial)
        return self

    def vertical_level(self, level):
        """Set vertical level for which data should be retrieved.

        The value depends on the coordinate values for the vertical dimension of the
        requested variable.

        This modifies the query in-place, but returns `self` so that multiple queries
        can be chained together on one line.

        Parameters
        ----------
        level : float
            The value of the desired level

        Returns
        -------
        self : NCSSQuery
            Returns self for chaining calls

        """
        return self.add_query_parameter(vertCoord=level)


#
# The remainder of the file is not considered part of the public API.
# Use at your own risk!
#

class ResponseRegistry(object):
    """Register functions to be called based on the mimetype in the response headers."""

    def __init__(self):
        """Initialize the registry."""
        self._reg = {}

    def register(self, mimetype):
        """Register a function to handle a particular mimetype."""
        def dec(func):
            self._reg[mimetype] = func
            return func
        return dec

    @staticmethod
    def default(content, units):  # pylint:disable=unused-argument
        """Handle a mimetype when no function is registered."""
        return content

    def __call__(self, resp, unit_handler):
        """Process the HTTP response using the appropriate handler."""
        mimetype = resp.headers['content-type'].split(';')[0]
        return self._reg.get(mimetype, self.default)(resp.content, unit_handler)


response_handlers = ResponseRegistry()


def squish(l):
    """If list contains only 1 element, return it instead."""
    return l if len(l) > 1 else l[0]


def combine_dicts(l):
    """Combine a list of dictionaries into single one."""
    ret = {}
    for item in l:
        ret.update(item)
    return ret


# Parsing of XML returns from NCSS
@response_handlers.register('application/xml')
def parse_xml(data, handle_units):
    """Parse XML data returned by NCSS."""
    root = ET.fromstring(data)
    return squish(parse_xml_dataset(root, handle_units))


def parse_xml_point(elem):
    """Parse an XML point tag."""
    point = {}
    units = {}
    for data in elem.findall('data'):
        name = data.get('name')
        unit = data.get('units')
        point[name] = float(data.text) if name != 'date' else parse_iso_date(data.text)
        if unit:
            units[name] = unit
    return point, units


def combine_xml_points(l, units, handle_units):
    """Combine multiple Point tags into an array."""
    ret = {}
    for item in l:
        for key, value in item.items():
            ret.setdefault(key, []).append(value)

    for key, value in ret.items():
        if key != 'date':
            ret[key] = handle_units(value, units.get(key, None))

    return ret


def parse_xml_dataset(elem, handle_units):
    """Create a netCDF-like dataset from XML data."""
    points, units = zip(*[parse_xml_point(p) for p in elem.findall('point')])
    # Group points by the contents of each point
    datasets = {}
    for p in points:
        datasets.setdefault(tuple(p.keys()), []).append(p)

    all_units = combine_dicts(units)
    return [combine_xml_points(d, all_units, handle_units) for d in datasets.values()]


# Handling of netCDF 3/4 from NCSS
try:
    from netCDF4 import Dataset
    from tempfile import NamedTemporaryFile

    @response_handlers.register('application/x-netcdf')
    @response_handlers.register('application/x-netcdf4')
    def read_netcdf(data, handle_units):  # pylint:disable=unused-argument
        """Handle HTTP responses in netCDF format."""
        ostype = platform.architecture()
        if ostype[1].lower() == 'windowspe':
            with NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(data)
                tmp_file.flush()
                atexit.register(deletetempfile, tmp_file.name)
                return Dataset(tmp_file.name, 'r')
        else:
            with NamedTemporaryFile() as tmp_file:
                tmp_file.write(data)
                tmp_file.flush()
                return Dataset(tmp_file.name, 'r')
except ImportError:
    import warnings
    warnings.warn('netCDF4 module not installed. '
                  'Will be unable to handle NetCDF returns from NCSS.')


def deletetempfile(fname):
    """Delete a temporary file.

    Warn on any exceptions.
    """
    try:
        remove(fname)
    except OSError:
        import warnings
        warnings.warn('temporary netcdf dataset file not deleted. '
                      'to delete temporary dataset file in the future '
                      'be sure to use dataset.close() when finished.')


# Parsing of CSV data returned from NCSS
@response_handlers.register('text/plain')
def parse_csv_response(data, unit_handler):
    """Handle CSV-formatted HTTP responses."""
    return squish([parse_csv_dataset(d, unit_handler) for d in data.split(b'\n\n')])


def parse_csv_header(line):
    """Parse the CSV header returned by TDS."""
    units = {}
    names = []
    for var in line.split(','):
        start = var.find('[')
        if start < 0:
            names.append(str(var))
            continue
        else:
            names.append(str(var[:start]))
        end = var.find(']', start)
        unitstr = var[start + 1:end]
        eq = unitstr.find('=')
        if eq >= 0:
            # go past = and ", skip final "
            units[names[-1]] = unitstr[eq + 2:-1]
    return names, units


def parse_csv_dataset(data, handle_units):
    """Parse CSV data into a netCDF-like dataset."""
    fobj = BytesIO(data)
    names, units = parse_csv_header(fobj.readline().decode('utf-8'))
    arrs = np.genfromtxt(fobj, dtype=None, names=names, delimiter=',', unpack=True,
                         converters={'date': lambda s: parse_iso_date(s.decode('utf-8'))})
    d = {}
    for f in arrs.dtype.fields:
        dat = arrs[f]
        if dat.dtype == np.object:
            dat = dat.tolist()
        d[f] = handle_units(dat, units.get(f, None))
    return d
