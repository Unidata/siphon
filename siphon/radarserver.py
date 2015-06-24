import xml.etree.ElementTree as ET
from collections import namedtuple

from .catalog import TDSCatalog
from .http_util import BadQueryError, DataQuery, HTTPEndPoint, urljoin


class RadarQuery(DataQuery):
    r'''An object representing a query to the THREDDS radar server.

    Expands on the queries supported by ``DataQuery`` to add queries specific to
    the radar data query service.
    '''

    def stations(self, *stns):
        r'''Specify one or more stations for the query.

        This modifies the query in-place, but returns ``self`` so that multiple
        queries can be chained together on one line.

        This replaces any existing spatial queries that have been set.

        Parameters
        ----------
        stns : one or more strings
            One or more names of variables to request

        Returns
        -------
        self : ``RadarQuery`` instance
            Returns self for chaining calls
        '''

        self._set_query(self.spatial_query, stn=stns)
        return self


class RadarServer(HTTPEndPoint):
    def _get_metadata(self):
        ds_cat = TDSCatalog(self.url_path('dataset.xml'))
        self.metadata = ds_cat.metadata
        self.variables = set(self.metadata['variables'].keys())
        self._get_stations()

    def _get_stations(self, station_file='stations.xml'):
        resp = self.get_path(station_file)
        self.stations = parse_station_table(ET.fromstring(resp.text))

    def query(self):
        r'''Returns a new query for the radar server

        Returns
        -------
        ``RadarQuery`` instance
        '''

        return RadarQuery()

    def validate_query(self, query):
        r'''Validate a query

        Determines whether `query` is well-formed. This includes checking for all
        required parameters, as well as checking parameters for valid values.

        Parameters
        ----------
        query : ``RadarQuery`` instance

        Returns
        -------
        valid : bool
            Whether `query` is valid.
        '''

        valid = True
        # Make sure all stations are in the table
        if 'stn' in query.spatial_query:
            valid = valid and all(stid in self.stations
                                  for stid in query.spatial_query['stn'])
        return valid

    def get_catalog(self, query):
        r'''Fetch a parsed THREDDS catalog from the radar server

        Requests a catalog of radar data files data from the radar server given the
        parameters in `query` and returns a ``TDSCatalog`` instance.

        Parameters
        ----------
        query : ``RadarQuery`` instance
            The parameters to send to the radar server

        Returns
        -------
        catalog : ``TDSCatalog`` instance
            The catalog of matching data files

        Raises
        ------
        BadQueryError
            When the query cannot be handled by the server

        See Also
        --------
        get_catalog_raw
        '''
        # TODO: Refactor TDSCatalog so we don't need two requests, or to do URL munging
        try:
            url = self._base[:-1] if self._base[-1] == '/' else self._base
            url += '?' + str(query)
            return TDSCatalog(url)
        except ET.ParseError:
            raise BadQueryError(self.get_catalog_raw(query))

    def get_catalog_raw(self, query):
        r'''Fetch THREDDS catalog XML from the radar server

        Requests a catalog of radar data files data from the radar server given the
        parameters in `query` and returns the raw XML.

        Parameters
        ----------
        query : ``RadarQuery`` instance
            The parameters to send to the radar server

        Returns
        -------
        catalog : bytes
            The XML of the catalog of matching data files

        See Also
        --------
        get_catalog
        '''

        return self.get_query(query).content


def get_radarserver_datasets(server):
    r'''Get datasets from a THREDDS radar server's top-level catalog.

    This is a helper function to construct the appropriate catalog URL from the
    server URL, fetch the catalog, and return the contained catalog references.

    Parameters
    ----------
    server : string
        The base URL to the THREDDS server

    Returns
    -------
    datasets : dict of string -> ``CatalogRef``
        Mapping of dataset name to the catalog reference
    '''
    if server[-1] != '/':
        server += '/'
    return TDSCatalog(urljoin(server, 'radarServer/catalog.xml')).catalog_refs


#
# The remainder of the file is not considered part of the public API.
# Use at your own risk!
#

Station = namedtuple('Station', 'id elevation latitude longitude name')


def parse_station_table(root):
    r'Parse station list XML file'
    stations = [parse_xml_station(elem) for elem in root.findall('station')]
    return {st.id: st for st in stations}


def parse_xml_station(elem):
    r'Create a ``Station`` instance from an XML tag'
    stid = elem.attrib['id']
    name = elem.find('name').text
    lat = elem.find('latitude').text
    lon = elem.find('longitude').text
    elev = elem.find('elevation').text
    return Station(id=stid, elevation=elev, latitude=lat, longitude=lon, name=name)
