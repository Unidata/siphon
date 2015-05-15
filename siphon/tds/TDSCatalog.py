from __future__ import print_function
import xml.etree.ElementTree as ET
from siphon import __version__ as ver

userAgent = 'siphon (%s)' % ver


class TDSCatalog(object):

    def __init__(self, catalog_url):
        # top level server url
        self.catalogUrl = catalog_url
        self.base_tds_url = catalog_url.split('/thredds/')[0]
        # get catalog.xml file
        xml_data = basic_http_request(catalog_url, return_response=True)
        # begin parsing the xml doc
        tree = ET.parse(xml_data)
        root = tree.getroot()
        if "name" in root.attrib:
            self.catalog_name = root.attrib["name"]
        else:
            self.catalog_name = "No name found"

        self.datasets = {}
        self.services = []
        self.catalogRefs = {}
        for child in root.iter():
            tag_type = child.tag.split('}')[-1]

            if tag_type == "service":
                if child.attrib["serviceType"] != "Compound":
                    self.services.append(SimpleService(child))
            elif tag_type == "dataset":
                if "urlPath" in child.attrib:
                    if child.attrib["urlPath"] == "latest.xml":
                        ds = Dataset(child, catalog_url)
                    else:
                        ds = Dataset(child)
                    self.datasets[ds.name] = ds
            elif tag_type == "catalogRef":
                catalog_ref = CatalogRef(child)
                self.catalogRefs[catalog_ref.title] = catalog_ref

        self.numberOfDatasets = len(self.datasets.keys())
        for dsName in self.datasets.keys():
            self.datasets[dsName].make_access_urls(
                self.base_tds_url, self.services)


class CatalogRef(object):
    def __init__(self, element_node):
        self.name = element_node.attrib["name"]
        self.href = element_node.attrib["{http://www.w3.org/1999/xlink}href"]
        if self.href[0] == '/':
            self.href = self.href[1:]
        self.title = element_node.attrib["{http://www.w3.org/1999/xlink}title"]


class Dataset(object):
    def __init__(self, element_node, catalog_url=""):
        self.name = element_node.attrib['name']
        self.urlPath = element_node.attrib['urlPath']
        self.resolved = False
        self.resolverUrl = None
        # if latest.xml, resolve the latest url
        if self.urlPath == "latest.xml":
            if catalog_url != "":
                self.resolved = True
                self.resolverUrl = self.urlPath
                self.urlPath = self.resolve_url(catalog_url)
            else:
                print("Must pass along the catalog URL to resolve the "
                      "latest.xml dataset!")

    def resolve_url(self, catalog_url):
        if catalog_url != "":
            resolver_base = catalog_url.split("catalog.xml")[0]
            resolver_url = resolver_base + self.urlPath
            resolver_xml = basic_http_request(resolver_url, return_response=True)
            tree = ET.parse(resolver_xml)
            root = tree.getroot()
            if "name" in root.attrib:
                self.catalog_name = root.attrib["name"]
            else:
                self.catalog_name = "No name found"

            found = False
            for child in root.iter():
                if not found:
                    tag_type = child.tag.split('}')[-1]
                    if tag_type == "dataset":
                        if "urlPath" in child.attrib:
                            ds = Dataset(child)
                            resolved_url = ds.urlPath
                            found = True
            if found:
                return resolved_url
            else:
                print("no dataset url path found in latest.xml!")

    def make_access_urls(self, catalog_url, services):
        access_urls = {}
        server_url = catalog_url.split('/thredds/')[0]
        for service in services:
            if service.serviceType != 'Resolver':
                access_urls[service.serviceType] = server_url + \
                    service.base + self.urlPath

        self.accessUrls = access_urls


class SimpleService(object):

    def __init__(self, service_node):
        self.name = service_node.attrib['name']
        self.serviceType = service_node.attrib['serviceType']
        self.base = service_node.attrib['base']


class CompoundService(object):

    def __init__(self, service_node):
        self.name = service_node.attrib['name']
        self.serviceType = service_node.attrib['serviceType']
        self.base = service_node.attrib['base']
        services = []
        for child in list(service_node):
            services.append(SimpleService(child))

        self.services = services


def basic_http_request(full_url, return_response=False):
    try:
        from urllib2 import urlopen, Request
    except ImportError:
        from urllib.request import urlopen, Request

    url_request = Request(full_url)
    url_request.add_header('User-agent', userAgent)
    try:
        response = urlopen(url_request)
        if return_response:
            return response
        else:
            del response
    except IOError as e:
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: {}'.format(e.reason))
            print('Full  url: {}'.format(full_url))
            raise
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: {}'.format(e.code))
            print('TDS response: {}'.format(e.read()))
            print('Full  url: {}'.format(full_url))
            raise
        else:
            print('error not caught!')
            raise


def get_latest_cat(cat):
    for service in cat.services:
        if (service.name.lower() == "latest" and
                service.serviceType.lower() == "resolver"):
            return TDSCatalog(cat.catalogUrl.replace("catalog.xml", "latest.xml"))

    print("ERROR: Latest Dataset Not Found!")


def get_latest_access_url(catalog, access_method):
    """
    Get the data access url, using a specified method, to the latest data
    available from a top level dataset TDSCatalog object.

    Parameters
    ----------
    catalog : TDSCatalog
        Instance of TDSCatalog - the THREDDS Data Server Catalog Object. The
        URL of the top level data catalog from a dataset should be used to
        create the object.

    access_method : String
        desired data access method (i.e. OPENDAP)

    Returns
    -------
    String
        String representation of the URL to be used to access the latest
        data available from a given catalog

    """

    latest_cat = get_latest_cat(catalog)
    if latest_cat != "":
        if len(latest_cat.datasets.keys()) == 1:
            latest_ds = latest_cat.datasets[latest_cat.datasets.keys()[0]]
            return latest_ds.accessUrls[access_method]
        else:
            print('ERROR: More than one access url matching the requested '
                  'access method...clearly this is an error')
