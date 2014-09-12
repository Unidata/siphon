import xml.etree.ElementTree as ET

userAgent = "pyudl"


class TDSCatalog():

    def __init__(self, catalogUrl):
        # top level server url
        self.catalogUrl = catalogUrl
        self.base_tds_url = catalogUrl.split('/thredds/')[0]
        # get catalog.xml file
        xml_data = basic_http_request(catalogUrl, return_response=True)
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
            tagType = child.tag.split('}')[-1]

            if tagType == "service":
                if child.attrib["serviceType"] != "Compound":
                    self.services.append(SimpleService(child))
            elif tagType == "dataset":
                if "urlPath" in child.attrib:
                    if child.attrib["urlPath"] == "latest.xml":
                        ds = Dataset(child, catalogUrl)
                    else:
                        ds = Dataset(child)
                    self.datasets[ds.name] = ds
            elif tagType == "catalogRef":
                catalogRef = CatalogRef(child)
                self.catalogRefs[catalogRef.title] = catalogRef

        self.numberOfDatasets = len(self.datasets.keys())
        for dsName in self.datasets.keys():
            self.datasets[dsName].makeAccessUrls(
                self.base_tds_url, self.services)


class CatalogRef():

    def __init__(self, elementNode):
        self.name = elementNode.attrib["name"]
        self.href = elementNode.attrib["{http://www.w3.org/1999/xlink}href"]
        if self.href[0] == '/':
            self.href = self.href[1:]
        self.title = elementNode.attrib["{http://www.w3.org/1999/xlink}title"]


class Dataset():

    def __init__(self, elementNode, catalogUrl=""):
        self.name = elementNode.attrib['name']
        self.urlPath = elementNode.attrib['urlPath']
        self.resolved = False
        self.resolverUrl = None
        # if latest.xml, resolve the latest url
        if self.urlPath == "latest.xml":
            if catalogUrl != "":
                self.resolved = True
                self.resolverUrl = self.urlPath
                self.urlPath = self.resolveUrl(catalogUrl)
            else:
                print "Must pass along the catalog URL to resolve the "
                print "latest.xml dataset!"

    def resolveUrl(self, catalogUrl):
        if catalogUrl != "":
            resolverBase = catalogUrl.split("catalog.xml")[0]
            resolverUrl = resolverBase + self.urlPath
            resolverXml = basic_http_request(resolverUrl, return_response=True)
            tree = ET.parse(resolverXml)
            root = tree.getroot()
            if "name" in root.attrib:
                self.catalog_name = root.attrib["name"]
            else:
                self.catalog_name = "No name found"

            found = False
            for child in root.iter():
                if not found:
                    tagType = child.tag.split('}')[-1]
                    if tagType == "dataset":
                        if "urlPath" in child.attrib:
                            ds = Dataset(child)
                            resolvedUrl = ds.urlPath
                            found = True
            if found:
                return resolvedUrl
            else:
                print "no dataset url path found in latest.xml!"

    def makeAccessUrls(self, catalogUrl, services):
        accessUrls = {}
        serverUrl = catalogUrl.split('/thredds/')[0]
        for service in services:
            if service.serviceType != 'Resolver':
                accessUrls[service.serviceType] = serverUrl + \
                    service.base + self.urlPath

        self.accessUrls = accessUrls


class SimpleService():

    def __init__(self, serviceNode):
        self.name = serviceNode.attrib['name']
        self.serviceType = serviceNode.attrib['serviceType']
        self.base = serviceNode.attrib['base']


class CompoundService():

    def __init__(self, serviceNode):
        self.name = serviceNode.attrib['name']
        self.serviceType = serviceNode.attrib['serviceType']
        self.base = serviceNode.attrib['base']
        services = []
        for child in list(serviceNode):
            services.append(SimpleService(child))

        self.services = services


def basic_http_request(full_url, return_response=False):
    import urllib2

    url_request = urllib2.Request(full_url)
    url_request.add_header('User-agent', userAgent)
    try:
        response = urllib2.urlopen(url_request)
        if return_response:
            return response
        else:
            del response
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: {}'.format(e.reason)
            print 'Full  url: {}'.format(full_url)
            raise
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: {}'.format(e.code)
            print 'TDS response: {}'.format(e.read())
            print 'Full  url: {}'.format(full_url)
            raise
        else:
            print 'error not caught!'
            raise

def get_latest_cat(cat):
    for service in cat.services:
        if (service.name.lower() == "latest" and service.serviceType.lower() == "resolver"):
            return TDSCatalog(cat.catalogUrl.replace("catalog.xml","latest.xml"))

    print "ERROR: Latest Dataset Not Found!"

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

    latestCat = get_latest_cat(catalog)
    if latestCat != "":
        if len(latestCat.datasets.keys()) == 1:
            latestDs = latestCat.datasets[latestCat.datasets.keys()[0]]
            return latestDs.accessUrls[access_method]
        else:
            print "ERROR: More than one access url matching the requested access method...clearly this is an error"

