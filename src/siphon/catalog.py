# Copyright (c) 2013-2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
Code to support reading and parsing catalog files from a THREDDS Data Server (TDS).

They help identifying the latest dataset and finding proper URLs to access the data.
"""

from collections import OrderedDict
from datetime import datetime
import logging
import re
from urllib.parse import urljoin, urlparse
import warnings
import xml.etree.ElementTree as ET  # noqa:N814

from .http_util import session_manager
from .metadata import TDSCatalogMetadata

log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)


class IndexableMapping(OrderedDict):
    """Extend ``OrderedDict`` to allow index-based access to values."""

    def __getitem__(self, item):
        """Return an item either by index or name."""
        try:
            item + ''  # Raises if item not a string
            return super().__getitem__(item)
        except TypeError:
            return list(self.values())[item]


class DatasetCollection(IndexableMapping):
    r"""Extend ``IndexableMapping`` to allow datetime-based filter queries.

    Indexing works like a dictionary. The dataset name ('my_data.nc', a string) is the key,
    and the value returned is an instance of ``Dataset``. Positional indexing
    (e.g., [0]) is another valid method of indexing.

    ``DatasetCollection`` is commonly encountered as the ``datasets`` attribute of a
    ``TDSCatalog``. If a ``regex`` in ``filter_time_nearest`` or ```filter_time_range` does not
    provide sufficient flexibility, or the ``TDSCatalog`` does not provide accurate times,
    iterating over ``datasets`` can be useful as part implementing a custom filter. For
    example, in ``for ds in catalog.datasets: print(ds)``, ``ds`` will be the dataset name, and
    ``ds`` can be used to implement further filtering logic.
    """

    default_regex = re.compile(r'(?P<year>\d{4})(?P<month>[01]\d)(?P<day>[0123]\d)_'
                               r'(?P<hour>[012]\d)(?P<minute>[0-5]\d)')

    def _get_datasets_with_times(self, regex, strptime=None):
        # Set the default regex if we don't have one
        # If strptime is provided, pass the regex group named 'strptime' to strptime
        regex = self.default_regex if regex is None else re.compile(regex)

        # Loop over the collection looking for keys that match our regex
        found_date = False
        for ds in self:
            match = regex.search(ds)

            # If we find one, make a datetime and yield it along with the value
            if match:
                found_date = True
                date_parts = match.groupdict()
                if strptime is not None:
                    date_str = date_parts.get('strptime', 0)
                    dt = datetime.strptime(date_str, strptime)
                else:
                    dt = datetime(int(date_parts.get('year', 0)),
                                  int(date_parts.get('month', 0)),
                                  int(date_parts.get('day', 0)),
                                  int(date_parts.get('hour', 0)),
                                  int(date_parts.get('minute', 0)),
                                  int(date_parts.get('second', 0)),
                                  int(date_parts.get('microsecond', 0)))
                yield dt, self[ds]

        # If we never found any keys that match, we should let the user know that rather
        # than have it be the same as if nothing matched filters
        if not found_date:
            raise ValueError('No datasets with times found.')

    def filter_time_nearest(self, time, regex=None, strptime=None):
        r"""Filter keys for an item closest to the desired time.

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
            given, this should contain either
            1. named groups: 'year', 'month', 'day', 'hour', 'minute', 'second',
            and 'microsecond', as appropriate. When a match is found, any of those groups
            missing from the pattern will be assigned a value of 0. The default pattern looks
            for patterns like: 20171118_2356.
            or
            2. a group named 'strptime' (e.g., r'_s(?P<strptime>\d{13})' for GOES-16 data)
            to be parsed with strptime.
        strptime : str, optional
            the format string that corresponds to regex option (2) above. For example, GOES-16
            data with a julian date matching the regex above is parsed with '%Y%j%H%M%S'.

        Returns
        -------
        Dataset
            The value with a time closest to that desired

        """
        return min(self._get_datasets_with_times(regex, strptime),
                   key=lambda i: abs((i[0] - time).total_seconds()))[-1]

    def filter_time_range(self, start, end, regex=None, strptime=None):
        r"""Filter keys for all items within the desired time range.

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
            given, this should contain either
            1. named groups: 'year', 'month', 'day', 'hour', 'minute', 'second',
            and 'microsecond', as appropriate. When a match is found, any of those groups
            missing from the pattern will be assigned a value of 0. The default pattern looks
            for patterns like: 20171118_2356.
            or
            2. a group named 'strptime' (e.g., r'_s(?P<strptime>\d{13})' for GOES-16 data)
            to be parsed with strptime.
        strptime : str, optional
            the format string that corresponds to regex option (2) above. For example, GOES-16
            data with a julian date matching the regex above is parsed with '%Y%j%H%M%S'.

        Returns
        -------
        List[Dataset]
            All values corresponding to times within the specified range

        """
        if start > end:
            warnings.warn('The provided start time comes after the end time. No data will '
                          'be returned.', UserWarning, stacklevel=2)
        return [item[-1] for item in self._get_datasets_with_times(regex, strptime)
                if start <= item[0] <= end]

    def __str__(self):
        """Return a string representation of the collection."""
        return str(list(self))

    __repr__ = __str__


def _try_lower(arg):
    try:
        arg = arg.lower()
    except (TypeError, AttributeError, ValueError):
        log.warning('Could not convert %s to lowercase.', arg)
    return arg


class CaseInsensitiveStr(str):
    """Extend ``str`` to use case-insensitive comparison and lookup."""

    def __init__(self, *args):
        """Create str with a _lowered property."""
        self._lowered = _try_lower(self)

    def __hash__(self):
        """Hash str using _lowered property."""
        return str.__hash__(self._lowered)

    def __eq__(self, other):
        """Return true if other is case-insensitive equal to self."""
        return str.__eq__(self._lowered, _try_lower(other))

    def __gt__(self, other):
        """Return true if other is case-insensitive greater than self."""
        return str.__gt__(self._lowered, _try_lower(other))

    def __ge__(self, other):
        """Return true if other is case-insensitive greater than or equal to self."""
        return str.__ge__(self._lowered, _try_lower(other))

    def __lt__(self, other):
        """Return true if other is case-insensitive less than self."""
        return str.__lt__(self._lowered, _try_lower(other))

    def __le__(self, other):
        """Return true if other is case-insensitive less than or equal to to self."""
        return str.__le__(self._lowered, _try_lower(other))

    def __ne__(self, other):
        """Return true if other is case-insensitive unequal to self."""
        return str.__ne__(self._lowered, _try_lower(other))


class CaseInsensitiveDict(dict):
    """Extend ``dict`` to use a case-insensitive key set."""

    def __init__(self, *args, **kwargs):
        """Create a dict with a set of lowercase keys."""
        super().__init__(*args, **kwargs)
        self._keys_to_lower()

    def __eq__(self, other):
        """Return true if other is case-insensitive equal to self."""
        return super().__eq__(CaseInsensitiveDict(other))

    def __getitem__(self, key):
        """Return value from case-insensitive lookup of ``key``."""
        return super().__getitem__(CaseInsensitiveStr(key))

    def __setitem__(self, key, value):
        """Set value with lowercase ``key``."""
        super().__setitem__(CaseInsensitiveStr(key), value)

    def __delitem__(self, key):
        """Delete value associated with case-insensitive lookup of ``key``."""
        return super().__delitem__(CaseInsensitiveStr(key))

    def __contains__(self, key):
        """Return true if key set includes case-insensitive ``key``."""
        return super().__contains__(CaseInsensitiveStr(key))

    def pop(self, key, *args, **kwargs):
        """Remove and return the value associated with case-insensitive ``key``."""
        return super().pop(CaseInsensitiveStr(key))

    def _keys_to_lower(self):
        """Convert key set to lowercase."""
        for k in list(self.keys()):
            val = super().__getitem__(k)
            super().__delitem__(k)
            self.__setitem__(CaseInsensitiveStr(k), val)


class TDSCatalog:
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
        self.session = session_manager.create_session()

        # get catalog.xml file
        resp = self.session.get(catalog_url)
        resp.raise_for_status()

        # top level server url
        self.catalog_url = resp.url
        self.base_tds_url = _find_base_tds_url(self.catalog_url)

        # If we were given an HTML link, warn about it and try to fix to xml
        if 'html' in resp.headers['content-type']:
            import warnings
            new_url = self.catalog_url.replace('html', 'xml')
            warnings.warn(f'URL {self.catalog_url} returned HTML. Changing to: {new_url}',
                          stacklevel=2)
            self.catalog_url = new_url
            resp = self.session.get(self.catalog_url)
            resp.raise_for_status()

        # begin parsing the xml doc
        root = ET.fromstring(resp.content)
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

                # see if the previously processed dataset has access elements as children
                # if so, these datasets need to be processed specially when making
                # access_urls
                if previous_dataset and self.datasets[previous_dataset].access_element_info:
                    self.ds_with_access_elements_to_process.append(previous_dataset)

                previous_dataset = current_dataset

            elif tag_type == 'access':
                self.datasets[current_dataset].add_access_element_info(child)
            elif tag_type == 'catalogRef':
                self._process_catalog_ref(child)
            elif (tag_type == 'metadata') or (tag_type == ''):
                self._process_metadata(child, tag_type)
            elif tag_type == 'service':
                if (CaseInsensitiveStr(child.attrib['serviceType'])
                        != CaseInsensitiveStr('Compound')):
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

        # Needed if the last dataset had such info, since it's only processed looking backwards
        # when a new dataset is encountered.
        if previous_dataset and self.datasets[previous_dataset].access_element_info:
            self.ds_with_access_elements_to_process.append(previous_dataset)

        self._process_datasets()

    def __str__(self):
        """Return a string representation of the catalog name."""
        return str(self.catalog_name)

    def __del__(self):
        """When TDSCatalog is deleted, close any open sessions."""
        self.session.close()

    def _process_dataset(self, element):
        catalog_url = ''
        if 'urlPath' in element.attrib and element.attrib['urlPath'] == 'latest.xml':
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
        # Need to use list (of keys) because we modify the dict while iterating
        for ds_name in list(self.datasets):
            # check to see if dataset needs to have access urls created, if not,
            # remove the dataset
            has_url_path = self.datasets[ds_name].url_path is not None
            is_ds_with_access_elements_to_process = (
                ds_name in self.ds_with_access_elements_to_process
            )
            if has_url_path or is_ds_with_access_elements_to_process:
                self.datasets[ds_name].make_access_urls(
                    self.base_tds_url, self.services, metadata=self.metadata)
            else:
                self.datasets.pop(ds_name)

    @property
    def latest(self):
        """Get the latest dataset, if available."""
        for service in self.services:
            if service.is_resolver():
                latest_cat = self.catalog_url.replace('catalog.xml', 'latest.xml')
                return TDSCatalog(latest_cat).datasets[0]
        raise AttributeError('"latest" not available for this catalog')

    __repr__ = __str__


class CatalogRef:
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
        self.title = element_node.attrib['{http://www.w3.org/1999/xlink}title']
        self.name = element_node.attrib.get('name', self.title)

        # Resolve relative URLs
        href = element_node.attrib['{http://www.w3.org/1999/xlink}href']
        self.href = urljoin(base_url, href)

    def __str__(self):
        """Return a string representation of the catalog reference."""
        return str(self.title)

    def follow(self):
        """Follow the catalog reference and return a new :class:`TDSCatalog`.

        Returns
        -------
        TDSCatalog
            The referenced catalog

        """
        return TDSCatalog(self.href)

    __repr__ = __str__


class Dataset:
    """
    An object for holding Datasets obtained from a THREDDS Client Catalog.

    Attributes
    ----------
    name : str
        The name of the :class:`Dataset` element
    url_path : str
        url to the accessible dataset
    access_urls : CaseInsensitiveDict[str, str]
        A dictionary of access urls whose keywords are the access service
        types defined in the catalog (for example, "OPENDAP", "NetcdfSubset",
        "WMS", etc.

    """

    ncss_service_names = (CaseInsensitiveStr('NetcdfSubset'),
                          CaseInsensitiveStr('NetcdfServer'))

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
        self.id = element_node.attrib.get('ID', None)
        self.url_path = element_node.attrib.get('urlPath', None)
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

    def __str__(self):
        """Return a string representation of the dataset."""
        return str(self.name)

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
            resolver_xml = session_manager.urlopen(resolver_url)
            tree = ET.parse(resolver_xml)
            root = tree.getroot()
            self.catalog_name = root.attrib.get('name', 'No name found')
            resolved_url = ''
            found = False
            for child in root.iter():
                if not found:
                    tag_type = child.tag.split('}')[-1]
                    if tag_type == 'dataset' and 'urlPath' in child.attrib:
                        ds = Dataset(child)
                        resolved_url = ds.url_path
                        found = True
            if found:
                return resolved_url
            else:
                log.warning('no dataset url path found in latest.xml!')
        return None

    def make_access_urls(self, catalog_url, all_services, metadata=None):
        """Make fully qualified urls for the access methods enabled on the dataset.

        Parameters
        ----------
        catalog_url : str
            The top level server url
        all_services : List[SimpleService]
            list of :class:`SimpleService` objects associated with the dataset
        metadata : dict
            Metadata from the :class:`TDSCatalog`

        """
        all_service_dict = CaseInsensitiveDict({})
        for service in all_services:
            all_service_dict[service.name] = service
            if isinstance(service, CompoundService):
                for subservice in service.services:
                    all_service_dict[subservice.name] = subservice

        service_name = metadata.get('serviceName', None)

        access_urls = CaseInsensitiveDict({})
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
                        server_base = urljoin(server_url, subservice.base)
                        access_urls[subservice.service_type] = server_base + self.url_path
                else:
                    server_base = urljoin(server_url, service.base)
                    access_urls[service.service_type] = server_base + self.url_path

        # process access children of dataset elements
        for sname in self.access_element_info:
            if sname in all_service_dict:
                service = all_service_dict[sname]
                url_path = self.access_element_info[sname]
                server_base = urljoin(server_url, service.base)
                access_urls[service.service_type] = server_base + url_path

        self.access_urls = access_urls

    def add_access_element_info(self, access_element):
        """Create an access method from a catalog element."""
        service_name = access_element.attrib['serviceName']
        url_path = access_element.attrib['urlPath']
        self.access_element_info[service_name] = url_path

    def download(self, filename=None):
        """Download the dataset to a local file.

        Parameters
        ----------
        filename : str, optional
            The full path to which the dataset will be saved

        """
        if filename is None:
            filename = self.name
        with self.remote_open() as infile, open(filename, 'wb') as outfile:
            outfile.write(infile.read())

    def remote_open(self, mode='b', encoding='ascii', errors='ignore'):
        """Open the remote dataset for random access.

        Get a file-like object for reading from the remote dataset, providing random access,
        similar to a local file.

        Parameters
        ----------
        mode : `'b'` or `'t'`, optional
            Mode with which to open the remote data; 'b' for binary, 't' for text. Defaults
            to 'b'.

        encoding : str, optional
            If ``mode`` is text, the encoding to use to decode the binary data into text.
            Defaults to 'ascii'.

        errors : str, optional
            If ``mode`` is text, the error handling behavior to pass to `bytes.decode`.
            Defaults to 'ignore'.

        Returns
        -------
        fobj : file-like object
            A random access, file-like object for reading data

        """
        fobj = self.access_with_service('HTTPServer')
        if mode == 't':
            from io import StringIO
            fobj = StringIO(fobj.read().decode(encoding, errors))
        return fobj

    def remote_access(self, service=None, use_xarray=None):
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

        if service not in (CaseInsensitiveStr('CdmRemote'), CaseInsensitiveStr('OPENDAP'),
                           CaseInsensitiveStr('DODS')):
            raise ValueError(service + ' is not a valid service for remote_access')

        return self.access_with_service(service, use_xarray)

    def subset(self, service=None):
        """Subset the dataset.

        Open the remote dataset and get a client for talking to ``service``.

        Parameters
        ----------
        service : str, optional
            The name of the service for subsetting the dataset. Defaults to 'NetcdfSubset'
            or 'NetcdfServer', in that order, depending on the services listed in the
            catalog.

        Returns
        -------
        a client for communicating using ``service``

        """
        if service is None:
            for service_name in self.ncss_service_names:
                if service_name in self.access_urls:
                    service = service_name
                    break
            else:
                raise RuntimeError('Subset access is not available for this dataset.')
        elif service not in self.ncss_service_names:
            raise ValueError(service + ' is not a valid service for subset. Options are: '
                             + ', '.join(self.ncss_service_names))

        return self.access_with_service(service)

    def access_with_service(self, service, use_xarray=None):
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
        service = CaseInsensitiveStr(service)
        if service == 'CdmRemote':
            if use_xarray:
                from .cdmr.xarray_support import CDMRemoteStore
                try:
                    import xarray as xr
                    provider = lambda url: xr.open_dataset(CDMRemoteStore(url))  # noqa: E731
                except ImportError:
                    raise ImportError('CdmRemote access needs xarray'
                                      'to be installed.') from None
            else:
                from .cdmr import Dataset as CDMRDataset
                provider = CDMRDataset
        elif service == 'OPENDAP' or service == 'DODS':
            if use_xarray:
                try:
                    import xarray as xr
                    provider = xr.open_dataset
                except ImportError:
                    raise ImportError('xarray needs to be installed if '
                                      '`use_xarray` is True.') from None
            else:
                try:
                    from netCDF4 import Dataset as NC4Dataset
                    provider = NC4Dataset
                except ImportError:
                    raise ImportError('OPENDAP access needs netCDF4-python'
                                      'to be installed.') from None
        elif service in self.ncss_service_names:
            from .ncss import NCSS
            provider = NCSS
        elif service == 'HTTPServer' or service == CaseInsensitiveStr('http'):
            provider = session_manager.urlopen
        else:
            raise ValueError(service + ' is not an access method supported by Siphon')

        try:
            return provider(self.access_urls[service])
        except KeyError:
            raise ValueError(service + ' is not available for this dataset') from None

    __repr__ = __str__


class SimpleService:
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
        self.service_type = CaseInsensitiveStr(service_node.attrib['serviceType'])
        self.base = service_node.attrib['base']
        self.access_urls = {}

    def is_resolver(self):
        """Return whether the service is a resolver service."""
        return self.service_type == 'Resolver'


class CompoundService:
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
        self.service_type = CaseInsensitiveStr(service_node.attrib['serviceType'])
        self.base = service_node.attrib['base']
        services = []
        subservices = 0
        for child in list(service_node):
            services.append(SimpleService(child))
            subservices += 1

        self.services = services
        self.number_of_subservices = subservices

    def is_resolver(self):
        """Return whether the service is a resolver service.

        For a compound service, this is always False because it will never be
        a resolver.
        """
        return False


def _find_base_tds_url(catalog_url):
    """Identify the base URL of the THREDDS server from the catalog URL.

    Will retain URL scheme, host, port and username/password when present.
    """
    scheme, netloc, *_ = urlparse(catalog_url)
    return scheme + '://' + netloc


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
