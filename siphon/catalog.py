# Copyright (c) 2013-2017 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
Code to support reading and parsing catalog files from a THREDDS Data Server (TDS).

They help identifying the latest dataset and finding proper URLs to access the data.
"""

from collections import OrderedDict
from datetime import datetime
import logging
import re
import xml.etree.ElementTree as ET
try:
    from urlparse import urljoin, urlparse
except ImportError:
    # Python 3
    from urllib.parse import urljoin, urlparse

from .http_util import create_http_session, urlopen
from .metadata import TDSCatalogMetadata

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())  # Python 2.7 needs a handler set
log.setLevel(logging.ERROR)


class IndexableMapping(OrderedDict):
    """Extend ``OrderedDict`` to allow index-based access to values."""

    def __getitem__(self, item):
        """Return an item either by index or name."""
        try:
            item + ''  # Raises if item not a string
            return super(IndexableMapping, self).__getitem__(item)
        except TypeError:
            return list(self.values())[item]


class DatasetCollection(IndexableMapping):
    """Extend ``IndexableMapping`` to allow datetime-based filter queries."""

    default_regex = re.compile(r'(?P<year>\d{4})(?P<month>[01]\d)(?P<day>[012]\d)_'
                               r'(?P<hour>[012]\d)(?P<minute>[0-5]\d)')

    def _get_datasets_with_times(self, regex):
        # Set the default regex if we don't have one
        if regex is None:
            regex = self.default_regex
        else:
            regex = re.compile(regex)

        # Loop over the collection looking for keys that match our regex
        found_date = False
        for ds in self:
            match = regex.search(ds)

            # If we find one, make a datetime and yield it along with the value
            if match:
                found_date = True
                date_parts = match.groupdict()
                dt = datetime(int(date_parts.get('year', 0)), int(date_parts.get('month', 0)),
                              int(date_parts.get('day', 0)), int(date_parts.get('hour', 0)),
                              int(date_parts.get('minute', 0)),
                              int(date_parts.get('second', 0)),
                              int(date_parts.get('microsecond', 0)))
                yield dt, self[ds]

        # If we never found any keys that match, we should let the user know that rather
        # than have it be the same as if nothing matched filters
        if not found_date:
            raise ValueError('No datasets with times found.')

    def filter_time_nearest(self, time, regex=None):
        """Filter keys for an item closest to the desired time.

        Loops over all keys in the collection and uses `regex` to extract and build
        `datetime`s. The collection of `datetime`s is compared to `start` and the value that
        has a `datetime` closest to that requested is returned.If none of the keys in the
        collection match the regex, indicating that the keys are not date/time-based,
        a ``ValueError`` is raised.

        Parameters
        ----------
        time : ``datetime.datetime``
            The desired time
        regex : str, optional
            The regular expression to use to extract date/time information from the key. If
            given, this should contain named groups: 'year', 'month', 'day', 'hour', 'minute',
            'second', and 'microsecond', as appropriate. When a match is found, any of those
            groups missing from the pattern will be assigned a value of 0. The default pattern
            looks for patterns like: 20171118_2356.

        Returns
        -------
            The value with a time closest to that desired

        """
        return min(self._get_datasets_with_times(regex),
                   key=lambda i: abs((i[0] - time).total_seconds()))[-1]

    def filter_time_range(self, start, end, regex=None):
        """Filter keys for all items within the desired time range.

        Loops over all keys in the collection and uses `regex` to extract and build
        `datetime`s. From the collection of `datetime`s, all values within `start` and `end`
        (inclusive) are returned. If none of the keys in the collection match the regex,
        indicating that the keys are not date/time-based, a ``ValueError`` is raised.

        Parameters
        ----------
        start : ``datetime.datetime``
            The start of the desired time range, inclusive
        end : ``datetime.datetime``
            The end of the desired time range, inclusive
        regex : str, optional
            The regular expression to use to extract date/time information from the key. If
            given, this should contain named groups: 'year', 'month', 'day', 'hour', 'minute',
            'second', and 'microsecond', as appropriate. When a match is found, any of those
            groups missing from the pattern will be assigned a value of 0. The default pattern
            looks for patterns like: 20171118_2356.

        Returns
        -------
            All values corresponding to times within the specified range

        """
        return [item[-1] for item in self._get_datasets_with_times(regex)
                if start <= item[0] <= end]


class TDSCatalog(object):
    """
    Parse information from a THREDDS Client Catalog.

    Attributes
    ----------
    catalog_url : str
        The url path of the catalog to parse.
    base_tds_url : str
        The top level server address
    datasets : DatasetCollection[str, Dataset]
        A dictionary of :class:`Dataset` objects, whose keys are the name of the
        dataset's name
    services : List
        A list of :class:`SimpleService` listed in the catalog
    catalog_refs : DatasetCollection[str, CatalogRef]
        A dictionary of :class:`CatalogRef` objects whose keys are the name of the
        catalog ref title.

    """

    def __init__(self, catalog_url):
        """
        Initialize the TDSCatalog object.

        Parameters
        ----------
        catalog_url : str
            The URL of a THREDDS client catalog

        """
        # top level server url
        self.catalog_url = catalog_url
        self.base_tds_url = _find_base_tds_url(catalog_url)

        session = create_http_session()

        # get catalog.xml file
        resp = session.get(self.catalog_url)
        resp.raise_for_status()

        # If we were given an HTML link, warn about it and try to fix to xml
        if 'html' in resp.headers['content-type']:
            import warnings
            new_url = self.catalog_url.replace('html', 'xml')
            warnings.warn('URL {} returned HTML. Changing to: {}'.format(self.catalog_url,
                                                                         new_url))
            self.catalog_url = new_url
            resp = session.get(self.catalog_url)
            resp.raise_for_status()

        # begin parsing the xml doc
        root = ET.fromstring(resp.text)
        self.catalog_name = root.attrib.get('name', 'No name found')

        self.datasets = DatasetCollection()
        self.services = []
        self.catalog_refs = DatasetCollection()
        self.metadata = {}
        self.ds_with_access_elements_to_process = []
        service_skip_count = 0
        service_skip = 0
        current_dataset = None
        previous_dataset = None
        for child in root.iter():
            tag_type = child.tag.split('}')[-1]
            if tag_type == 'dataset':
                current_dataset = child.attrib['name']
                self._process_dataset(child)

                if previous_dataset:
                    # see if the previously processed dataset has access elements as children
                    # if so, these datasets need to be processed specially when making
                    # access_urls
                    if self.datasets[previous_dataset].access_element_info:
                        self.ds_with_access_elements_to_process.append(previous_dataset)

                previous_dataset = current_dataset

            elif tag_type == 'access':
                self.datasets[current_dataset].add_access_element_info(child)
            elif tag_type == 'catalogRef':
                self._process_catalog_ref(child)
            elif (tag_type == 'metadata') or (tag_type == ''):
                self._process_metadata(child, tag_type)
            elif tag_type == 'service':
                if child.attrib['serviceType'] != 'Compound':
                    # we do not want to process single services if they
                    # are already contained within a compound service, so
                    # we need to skip over those cases.
                    if service_skip_count >= service_skip:
                        self.services.append(SimpleService(child))
                        service_skip = 0
                        service_skip_count = 0
                    else:
                        service_skip_count += 1
                else:
                    self.services.append(CompoundService(child))
                    service_skip = self.services[-1].number_of_subservices
                    service_skip_count = 0

        self._process_datasets()

    def _process_dataset(self, element):
        catalog_url = ''
        if 'urlPath' in element.attrib:
            if element.attrib['urlPath'] == 'latest.xml':
                catalog_url = self.catalog_url

        ds = Dataset(element, catalog_url=catalog_url)
        self.datasets[ds.name] = ds

    def _process_catalog_ref(self, element):
        catalog_ref = CatalogRef(self.catalog_url, element)
        self.catalog_refs[catalog_ref.title] = catalog_ref

    def _process_metadata(self, element, tag_type):
        if tag_type == '':
            log.warning('Trying empty tag type as metadata')
        self.metadata = TDSCatalogMetadata(element, self.metadata).metadata

    def _process_datasets(self):
        for dsName in list(self.datasets.keys()):
            # check to see if dataset needs to have access urls created, if not,
            # remove the dataset
            has_url_path = self.datasets[dsName].url_path is not None
            is_ds_with_access_elements_to_process = \
                dsName in self.ds_with_access_elements_to_process
            if has_url_path or is_ds_with_access_elements_to_process:
                self.datasets[dsName].make_access_urls(
                    self.base_tds_url, self.services, metadata=self.metadata)
            else:
                self.datasets.pop(dsName)

    @property
    def latest(self):
        """Get the latest dataset, if available."""
        for service in self.services:
            if service.is_resolver():
                latest_cat = self.catalog_url.replace('catalog.xml', 'latest.xml')
                return TDSCatalog(latest_cat).datasets[0]
        raise AttributeError('"latest" not available for this catalog')


class CatalogRef(object):
    """
    An object for holding catalog references obtained from a THREDDS Client Catalog.

    Attributes
    ----------
    name : str
        The name of the :class:`CatalogRef` element
    href : str
        url to the :class:`CatalogRef`'s THREDDS Client Catalog
    title : str
        Title of the :class:`CatalogRef` element

    """

    def __init__(self, base_url, element_node):
        """
        Initialize the catalogRef object.

        Parameters
        ----------
        base_url : str
            URL to the base catalog that owns this reference
        element_node : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing a catalogRef node

        """
        self.name = element_node.attrib['name']
        self.title = element_node.attrib['{http://www.w3.org/1999/xlink}title']

        # Resolve relative URLs
        href = element_node.attrib['{http://www.w3.org/1999/xlink}href']
        self.href = urljoin(base_url, href)

    def follow(self):
        """Follow the catalog reference and return a new :class:`TDSCatalog`.

        Returns
        -------
        TDSCatalog
            The referenced catalog

        """
        return TDSCatalog(self.href)


class Dataset(object):
    """
    An object for holding Datasets obtained from a THREDDS Client Catalog.

    Attributes
    ----------
    name : str
        The name of the :class:`Dataset` element
    url_path : str
        url to the accessible dataset
    access_urls : dict[str, str]
        A dictionary of access urls whose keywords are the access service
        types defined in the catalog (for example, "OPENDAP", "NetcdfSubset",
        "WMS", etc.

    """

    def __init__(self, element_node, catalog_url=''):
        """Initialize the Dataset object.

        Parameters
        ----------
        element_node : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing a Dataset node
        catalog_url : str
            The top level server url

        """
        self.name = element_node.attrib['name']
        if 'urlPath' in element_node.attrib:
            self.url_path = element_node.attrib['urlPath']
        else:
            self.url_path = None
        self.catalog_name = ''
        self.access_element_info = {}
        self._resolved = False
        self._resolverUrl = None
        # if latest.xml, resolve the latest url
        if self.url_path == 'latest.xml':
            if catalog_url != '':
                self._resolved = True
                self._resolverUrl = self.url_path
                self.url_path = self.resolve_url(catalog_url)
            else:
                log.warning('Must pass along the catalog URL to resolve '
                            'the latest.xml dataset!')

    def resolve_url(self, catalog_url):
        """Resolve the url of the dataset when reading latest.xml.

        Parameters
        ----------
        catalog_url : str
            The catalog url to be resolved

        """
        if catalog_url != '':
            resolver_base = catalog_url.split('catalog.xml')[0]
            resolver_url = resolver_base + self.url_path
            resolver_xml = urlopen(resolver_url)
            tree = ET.parse(resolver_xml)
            root = tree.getroot()
            if 'name' in root.attrib:
                self.catalog_name = root.attrib['name']
            else:
                self.catalog_name = 'No name found'
            resolved_url = ''
            found = False
            for child in root.iter():
                if not found:
                    tag_type = child.tag.split('}')[-1]
                    if tag_type == 'dataset':
                        if 'urlPath' in child.attrib:
                            ds = Dataset(child)
                            resolved_url = ds.url_path
                            found = True
            if found:
                return resolved_url
            else:
                log.warning('no dataset url path found in latest.xml!')

    def make_access_urls(self, catalog_url, all_services, metadata=None):
        """Make fully qualified urls for the access methods enabled on the dataset.

        Parameters
        ----------
        catalog_url : str
            The top level server url
        all_services : List[SimpleService]
            list of :class:`SimpleService` objects associated with the dataset
        metadata : TDSCatalogMetadata
            Metadata from the :class:`TDSCatalog`

        """
        all_service_dict = {service.name: service for service in all_services}
        service_name = None
        if metadata:
            if 'serviceName' in metadata:
                service_name = metadata['serviceName']

        access_urls = {}
        server_url = _find_base_tds_url(catalog_url)

        # process access urls for datasets that reference top
        # level catalog services (individual or compound service
        # types).
        if service_name in all_service_dict:
            service = all_service_dict[service_name]
            if service.service_type != 'Resolver':
                # if service is a CompoundService, create access url
                # for each SimpleService
                if isinstance(service, CompoundService):
                    for subservice in service.services:
                        access_urls[subservice.service_type] = (server_url +
                                                                subservice.base +
                                                                self.url_path)
                else:
                    access_urls[service.service_type] = (server_url +
                                                         service.base +
                                                         self.url_path)

        # process access children of dataset elements
        for service_type in self.access_element_info:
            url_path = self.access_element_info[service_type]
            if service_type in all_service_dict:
                access_urls[service_type] = (server_url +
                                             all_service_dict[service_type].base +
                                             url_path)

        self.access_urls = access_urls

    def add_access_element_info(self, access_element):
        """Create an access method from a catalog element."""
        service_name = access_element.attrib['serviceName']
        url_path = access_element.attrib['urlPath']
        self.access_element_info[service_name] = url_path

    def download(self, filename):
        """Download the dataset to a local file.

        Parameters
        ----------
        filename : str
            The full path to which the dataset will be saved

        """
        with self.remote_open() as infile:
            with open(filename, 'wb') as outfile:
                outfile.write(infile.read())

    def remote_open(self):
        """Open the remote dataset for random access.

        Get a file-like object for reading from the remote dataset, providing random access,
        similar to a local file.

        Returns
        -------
        A random access, file-like object

        """
        return self.access_with_service('HTTPServer')

    def remote_access(self, service=None):
        """Access the remote dataset.

        Open the remote dataset and get a netCDF4-compatible `Dataset` object providing
        index-based subsetting capabilities.

        Parameters
        ----------
        service : str, optional
            The name of the service to use for access to the dataset, either
            'CdmRemote' or 'OPENDAP'. Defaults to 'CdmRemote'.

        Returns
        -------
        Dataset
            Object for netCDF4-like access to the dataset

        """
        if service is None:
            service = 'CdmRemote' if 'CdmRemote' in self.access_urls else 'OPENDAP'

        if service not in ('CdmRemote', 'OPENDAP'):
            raise ValueError(service + ' is not a valid service for remote_access')

        return self.access_with_service(service)

    def subset(self, service=None):
        """Subset the dataset.

        Open the remote dataset and get a client for talking to ``service``.

        Parameters
        ----------
        service : str, optional
            The name of the service for subsetting the dataset. Defaults to 'NetcdfSubset'.

        Returns
        -------
        a client for communicating using ``service``

        """
        if service is None:
            service = 'NetcdfSubset'

        if service not in ('NetcdfSubset',):
            raise ValueError(service + ' is not a valid service for subset')

        return self.access_with_service(service)

    def access_with_service(self, service):
        """Access the dataset using a particular service.

        Return an Python object capable of communicating with the server using the particular
        service. For instance, for 'HTTPServer' this is a file-like object capable of
        HTTP communication; for OPENDAP this is a netCDF4 dataset.

        Parameters
        ----------
        service : str
            The name of the service for accessing the dataset

        Returns
        -------
            An instance appropriate for communicating using ``service``.

        """
        if service == 'CdmRemote':
            from .cdmr import Dataset as CDMRDataset
            provider = CDMRDataset
        elif service == 'OPENDAP':
            try:
                from netCDF4 import Dataset as NC4Dataset
                provider = NC4Dataset
            except ImportError:
                raise ImportError('OPENDAP access requires netCDF4-python to be installed.')
        elif service == 'NetcdfSubset':
            from .ncss import NCSS
            provider = NCSS
        elif service == 'HTTPServer':
            provider = urlopen
        else:
            raise ValueError(service + ' is not an access method supported by Siphon')

        try:
            return provider(self.access_urls[service])
        except KeyError:
            raise ValueError(service + ' is not available for this dataset')


class SimpleService(object):
    """Hold information about an access service enabled on a dataset.

    Attributes
    ----------
    name : str
        The name of the service
    service_type : str
        The service type (i.e. "OPENDAP", "NetcdfSubset", "WMS", etc.)
    access_urls : dict[str, str]
        A dictionary of access urls whose keywords are the access service
        types defined in the catalog (for example, "OPENDAP", "NetcdfSubset",
        "WMS", etc.)

    """

    def __init__(self, service_node):
        """Initialize the Dataset object.

        Parameters
        ----------
        service_node : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing a service node

        """
        self.name = service_node.attrib['name']
        self.service_type = service_node.attrib['serviceType']
        self.base = service_node.attrib['base']
        self.access_urls = {}

    def is_resolver(self):
        """Return whether the service is a resolver service."""
        return self.service_type.lower() == 'resolver'


class CompoundService(object):
    """Hold information about compound services.

    Attributes
    ----------
    name : str
        The name of the compound service
    service_type : str
        The service type (for this object, service type will always be
        "COMPOUND")
    services : list[SimpleService]
        A list of :class:`SimpleService` objects

    """

    def __init__(self, service_node):
        """Initialize a :class:`CompoundService` object.

        Parameters
        ----------
        service_node : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing a compound service node

        """
        self.name = service_node.attrib['name']
        self.service_type = service_node.attrib['serviceType']
        self.base = service_node.attrib['base']
        services = []
        subservices = 0
        for child in list(service_node):
            services.append(SimpleService(child))
            subservices += 1

        self.services = services
        self.number_of_subservices = subservices


def _find_base_tds_url(catalog_url):
    """Identify the base URL of the THREDDS server from the catalog URL.

    Will retain URL scheme, host, port and username/password when present.
    """
    url_components = urlparse(catalog_url)
    if url_components.path:
        return catalog_url.split(url_components.path)[0]
    else:
        return catalog_url


def get_latest_access_url(catalog_url, access_method):
    """Get the data access url to the latest data using a specified access method.

    These are available for a data available from a top level dataset catalog (url).
    Currently only supports the existence of one "latest" dataset.

    Parameters
    ----------
    catalog_url : str
        The URL of a top level data catalog
    access_method : str
        desired data access method (i.e. "OPENDAP", "NetcdfSubset", "WMS", etc)

    Returns
    -------
    access_url : str
        Data access URL to be used to access the latest data available from a
        given catalog using the specified `access_method`. Typically a single string,
        but not always.

    """
    return TDSCatalog(catalog_url).latest.access_urls[access_method]
