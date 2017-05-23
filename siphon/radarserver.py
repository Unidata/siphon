# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Support making data requests to the radar data query service (radar server) on a TDS.

This includes forming proper queries as well as parsing the returned catalog.
"""

from collections import namedtuple
import xml.etree.ElementTree as ET

from .catalog import TDSCatalog
from .http_util import BadQueryError, DataQuery, HTTPEndPoint, urljoin


class RadarQuery(DataQuery):
    """Represent a query to the THREDDS radar server.

    Expands on the queries supported by :class:`~siphon.http_util.DataQuery` to add queries
    specific to the radar data query service.
    """

    def stations(self, *stns):
        """Specify one or more stations for the query.

        This modifies the query in-place, but returns `self` so that multiple
        queries can be chained together on one line.

        This replaces any existing spatial queries that have been set.

        Parameters
        ----------
        stns : one or more strings
            One or more names of variables to request

        Returns
        -------
        self : RadarQuery
            Returns self for chaining calls

        """
        self._set_query(self.spatial_query, stn=stns)
        return self


class RadarServer(HTTPEndPoint):
    """Wrap access to the THREDDS radar query service (radar server).

    Simplifies access via HTTP to the radar server endpoint. Parses the metadata, provides
    query catalog results download and parsing based on the appropriate query.

    Attributes
    ----------
    metadata : :class:`~siphon.metadata.TDSCatalogMetadata`
        Contains the result of parsing the radar server endpoint's dataset.xml. This has
        information about the time and space coverage, as well as full information
        about all of the variables.
    variables : set(str)
        Names of all variables available in this dataset
    stations : dict[str, Station]
        Mapping of station ID to a :class:`Station`, which is a namedtuple containing the
        station's id, name, latitude, longitude, and elevation.

    """

    def __init__(self, url):
        """Create a RadarServer instance.

        Parameters
        ----------
        url : str
            The base URL for the endpoint

        """
        xmlfile = '/dataset.xml'
        if url.endswith(xmlfile):
            url = url[:-len(xmlfile)]
        super(RadarServer, self).__init__(url)

    def _get_metadata(self):
        ds_cat = TDSCatalog(self.url_path('dataset.xml'))
        self.metadata = ds_cat.metadata
        self.variables = {k.split('/')[0] for k in self.metadata['variables'].keys()}
        self._get_stations()

    def _get_stations(self, station_file='stations.xml'):
        resp = self.get_path(station_file)
        self.stations = parse_station_table(ET.fromstring(resp.text))

    def query(self):
        """Return a new query for the radar server.

        Returns
        -------
        RadarQuery
            The new query

        """
        return RadarQuery()

    def validate_query(self, query):
        """Validate a query.

        Determines whether `query` is well-formed. This includes checking for all
        required parameters, as well as checking parameters for valid values.

        Parameters
        ----------
        query : RadarQuery
            The query to validate

        Returns
        -------
        valid : bool
            Whether `query` is valid.

        """
        valid = True
        # Make sure all stations are in the table
        if 'stn' in query.spatial_query:
            valid = valid and all(stid in self.stations
                                  for stid in query.spatial_query['stn'])

        if query.var:
            valid = valid and all(var in self.variables for var in query.var)

        return valid

    def get_catalog(self, query):
        """Fetch a parsed THREDDS catalog from the radar server.

        Requests a catalog of radar data files data from the radar server given the
        parameters in `query` and returns a :class:`~siphon.catalog.TDSCatalog` instance.

        Parameters
        ----------
        query : RadarQuery
            The parameters to send to the radar server

        Returns
        -------
        catalog : TDSCatalog
            The catalog of matching data files

        Raises
        ------
        :class:`~siphon.http_util.BadQueryError`
            When the query cannot be handled by the server

        See Also
        --------
        get_catalog_raw

        """
        # TODO: Refactor TDSCatalog so we don't need two requests, or to do URL munging
        try:
            url = self._base[:-1] if self._base[-1] == '/' else self._base
            url += '?' + str(query)
            return TDSCatalog(url)
        except ET.ParseError:
            raise BadQueryError(self.get_catalog_raw(query))

    def get_catalog_raw(self, query):
        """Fetch THREDDS catalog XML from the radar server.

        Requests a catalog of radar data files data from the radar server given the
        parameters in `query` and returns the raw XML.

        Parameters
        ----------
        query : RadarQuery
            The parameters to send to the radar server

        Returns
        -------
        catalog : bytes
            The XML of the catalog of matching data files

        See Also
        --------
        get_catalog

        """
        return self.get_query(query).content


def get_radarserver_datasets(server):
    """Get datasets from a THREDDS radar server's top-level catalog.

    This is a helper function to construct the appropriate catalog URL from the
    server URL, fetch the catalog, and return the contained catalog references.

    Parameters
    ----------
    server : string
        The base URL to the THREDDS server

    Returns
    -------
    datasets : dict[str, :class:`~siphon.catalog.CatalogRef`]
        Mapping of dataset name to the catalog reference

    """
    if server[-1] != '/':
        server += '/'
    return TDSCatalog(urljoin(server, 'radarServer/catalog.xml')).catalog_refs


#
# The remainder of the file is not considered part of the public API.
# Use at your own risk!
#

Station = namedtuple('Station', 'id elevation latitude longitude name')


def parse_station_table(root):
    """Parse station list XML file."""
    stations = [parse_xml_station(elem) for elem in root.findall('station')]
    return {st.id: st for st in stations}


def parse_xml_station(elem):
    """Create a :class:`Station` instance from an XML tag."""
    stid = elem.attrib['id']
    name = elem.find('name').text
    lat = float(elem.find('latitude').text)
    lon = float(elem.find('longitude').text)
    elev = float(elem.find('elevation').text)
    return Station(id=stid, elevation=elev, latitude=lat, longitude=lon, name=name)
