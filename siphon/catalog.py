import logging
import xml.etree.ElementTree as ET

from .metadata import TDSCatalogMetadata
from .http_util import urlopen

log = logging.getLogger("siphon.catalog")
log.setLevel(logging.WARNING)


class TDSCatalog(object):
    r"""
    An object for holding information from a THREDDS Client Catalog.


    Attributes
    ----------
    catalog_url : string
        The url path of the catalog to parse.
    base_tds_url : string
        The top level server address
    datasets : Dataset
        A dictionary of Dataset object, whose keys are the name of the
        dataset's name
    services : List
        A list of SimpleServices listed in the catalog
    catalog_refs : dict
        A dictionary of CatalogRef objects whose keys are the name of the
        catalog ref title.

    """
    def __init__(self, catalog_url):
        r"""
        Initialize the TDSCatalog object.

        Parameters
        ----------
        catalog_url : string
            The URL of a THREDDS client catalog
        """
        # top level server url
        self.catalog_url = catalog_url
        self.base_tds_url = catalog_url.split('/thredds/')[0]
        # get catalog.xml file
        xml_fobj = urlopen(catalog_url)
        # begin parsing the xml doc
        tree = ET.parse(xml_fobj)
        root = tree.getroot()
        if "name" in root.attrib:
            self.catalog_name = root.attrib["name"]
        else:
            self.catalog_name = "No name found"

        self.datasets = {}
        self.services = []
        self.catalog_refs = {}
        self.metadata = {}
        service_skip_count = 0
        service_skip = 0
        for child in root.iter():
            tag_type = child.tag.split('}')[-1]
            if tag_type == "dataset":
                self._process_dataset(child)
            elif tag_type == "catalogRef":
                self._process_catalog_ref(child)
            elif (tag_type == "metadata") or (tag_type == ""):
                self._process_metadata(child, tag_type)
            elif tag_type == "service":
                if child.attrib["serviceType"] != "Compound":
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
        if "urlPath" in element.attrib:
            if element.attrib["urlPath"] == "latest.xml":
                ds = Dataset(element, self.catalog_url)
            else:
                ds = Dataset(element)
            self.datasets[ds.name] = ds

    def _process_catalog_ref(self, element):
        catalog_ref = CatalogRef(element)
        self.catalog_refs[catalog_ref.title] = catalog_ref

    def _process_metadata(self, element, tag_type):
        if tag_type == "":
            log.warning("Trying empty tag type as metadata")
        self.metadata = TDSCatalogMetadata(element, self.metadata).metadata

    def _process_datasets(self):
        for dsName in list(self.datasets.keys()):
            self.datasets[dsName].make_access_urls(
                self.base_tds_url, self.services, metadata=self.metadata)


class CatalogRef(object):
    r"""
    An object for holding Catalog References obtained from a THREDDS Client
    Catalog.


    Attributes
    ----------
    name : string
        The name of the catalogRef element
    href : string
        url to the catalogRef's THREDDS Client Catalog
    title : string
        Title of the catalogRef element
    """
    def __init__(self, element_node):
        r"""
        Initialize the catalogRef object.

        Parameters
        ----------
        element_node : Element
            An Element Tree Element representing a catalogRef node

        """
        self.name = element_node.attrib["name"]
        self.href = element_node.attrib["{http://www.w3.org/1999/xlink}href"]
        if self.href[0] == '/':
            self.href = self.href[1:]
        self.title = element_node.attrib["{http://www.w3.org/1999/xlink}title"]


class Dataset(object):
    r"""
    An object for holding Datasets obtained from a THREDDS Client Catalog.


    Attributes
    ----------
    name : string
        The name of the Dataset element
    url_path : string
        url to the accessible dataset
    access_urls : dict
        A dictionary of access urls whose keywords are the access service
        types defined in the catalog (for example, "OPENDAP", "NetcdfSubset",
        "WMS", etc.
    """
    def __init__(self, element_node, catalog_url=""):
        r"""
        Initialize the Dataset object.

        Parameters
        ----------
        element_node : Element
            An Element Tree Element representing a Dataset node
        catalog_url : string
            The top level server url

        """
        self.name = element_node.attrib['name']
        self.url_path = element_node.attrib['urlPath']
        self._resolved = False
        self._resolverUrl = None
        # if latest.xml, resolve the latest url
        if self.url_path == "latest.xml":
            if catalog_url != "":
                self._resolved = True
                self._resolverUrl = self.url_path
                self.url_path = self.resolve_url(catalog_url)
            else:
                log.warning('Must pass along the catalog URL to resolve '
                            'the latest.xml dataset!')

    def resolve_url(self, catalog_url):
        r"""
        Resolve the url of the dataset when reading latest.xml

        Parameters
        ----------
        catalog_url : string
            The catalog url to be resolved

        """
        if catalog_url != "":
            resolver_base = catalog_url.split("catalog.xml")[0]
            resolver_url = resolver_base + self.url_path
            resolver_xml = urlopen(resolver_url)
            tree = ET.parse(resolver_xml)
            root = tree.getroot()
            if "name" in root.attrib:
                self.catalog_name = root.attrib["name"]
            else:
                self.catalog_name = "No name found"
            resolved_url = ''
            found = False
            for child in root.iter():
                if not found:
                    tag_type = child.tag.split('}')[-1]
                    if tag_type == "dataset":
                        if "urlPath" in child.attrib:
                            ds = Dataset(child)
                            resolved_url = ds.url_path
                            found = True
            if found:
                return resolved_url
            else:
                log.warning("no dataset url path found in latest.xml!")

    def make_access_urls(self, catalog_url, all_services, metadata=None):
        r"""
        Make fully qualified urls for the access methods enabled on the
        dataset.

        Parameters
        ----------
        catalog_url : string
            The top level server url

        services : list
            list of SimpleService objects associated with the dataset

        """
        service_name = None
        if metadata:
            if "serviceName" in metadata:
                service_name = metadata["serviceName"]

        access_urls = {}
        server_url = catalog_url.split('/thredds/')[0]

        found_service = None
        if service_name:
            for service in all_services:
                if service.name == service_name:
                    found_service = service
                    break

        service = found_service
        if service:
            if service.service_type != 'Resolver':
                if isinstance(service, CompoundService):
                    for subservice in service.services:
                        access_urls[subservice.service_type] = server_url + \
                            subservice.base + self.url_path
                else:
                    access_urls[service.service_type] = server_url + \
                        service.base + self.url_path

        self.access_urls = access_urls


class SimpleService(object):
    r"""
    An object for holding information about an access service enabled on a
    dataset.


    Attributes
    ----------
    name : string
        The name of the service
    service_type : string
        The service type (i.e. "OPENDAP", "NetcdfSubset", "WMS", etc.)
    access_urls : dict
        A dictionary of access urls whose keywords are the access service
        types defined in the catalog (for example, "OPENDAP", "NetcdfSubset",
        "WMS", etc.)
    """
    def __init__(self, service_node):
        r"""
        Initialize the Dataset object.

        Parameters
        ----------
        service_node : Element
            An Element Tree Element representing a service node

        """
        self.name = service_node.attrib['name']
        self.service_type = service_node.attrib['serviceType']
        self.base = service_node.attrib['base']


class CompoundService(object):
    r"""
    An object for holding information about an Compound services.


    Attributes
    ----------
    name : string
        The name of the compound service
    service_type : string
        The service type (for this object, service type will always be
        "COMPOUND")
    services : list
        A list of SimpleService objects
    """
    def __init__(self, service_node):
        r"""
        Initialize a CompoundService object.

        Parameters
        ----------
        service_node : Element
            An Element Tree Element representing a compound service node

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


def _get_latest_cat(catalog_url):
    r"""
    Get the latest dataset catalog from the supplied top level dataset catalog
    url.

    Parameters
    ----------
    catalog_url : string
        The URL of a top level data catalog

    access_method : String
        desired data access method (i.e. "OPENDAP", "NetcdfSubset", "WMS", etc)

    Returns
    -------
    TDSCatalog
        A TDSCatalog object containing the information from the latest dataset

    """
    cat = TDSCatalog(catalog_url)
    for service in cat.services:
        if (service.name.lower() == "latest" and
                service.service_type.lower() == "resolver"):
            latest_cat = cat.catalog_url.replace("catalog.xml", "latest.xml")
            return TDSCatalog(latest_cat)

    log.error('ERROR: "latest" service not enabled for this catalog!')


def get_latest_access_url(catalog_url, access_method):
    r"""
    Get the data access url, using a specified access method, to the latest
    data available from a top level dataset catalog (url). Currently only
    supports the existence of one "latest" dataset.

    Parameters
    ----------
    catalog_url : string
        The URL of a top level data catalog

    access_method : String
        desired data access method (i.e. "OPENDAP", "NetcdfSubset", "WMS", etc)

    Returns
    -------
    string
        Data access URL to be used to access the latest data available from a
        given catalog using the specified `access_method`. Typical of length 1,
        but not always.

    """

    latest_cat = _get_latest_cat(catalog_url)
    if latest_cat != "":
        if len(list(latest_cat.datasets.keys())) > 0:
            latest_ds = []
            for lds_name in latest_cat.datasets:
                lds = latest_cat.datasets[lds_name]
                if access_method in lds.access_urls:
                    latest_ds.append(lds.access_urls[access_method])
            if len(latest_ds) == 1:
                latest_ds = latest_ds[0]
                return latest_ds
            else:
                log.error('ERROR: More than one latest dataset found '
                          'this case is currently not suppored in '
                          'siphon.')
        else:
            log.error('ERROR: More than one access url matching the '
                      'requested access method...clearly this is an error')
