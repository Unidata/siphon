import xml.etree.ElementTree as ET

userAgent = "pyudl"

class TDSCatalog():
    def __init__(self, catalogUrl):
        # top level server url
        self.catalogUrl = catalogUrl
        self.base_tds_url = catalogUrl.split('/thredds/')[0]
        # get catalog.xml file
        xml_data = basic_http_request(catalogUrl, return_response = True)
        # begin parsing the xml doc
        tree = ET.parse(xml_data)
        root = tree.getroot()
        if root.attrib.has_key("name"):
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
                if child.attrib.has_key("urlPath"):
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
            self.datasets[dsName].makeAccessUrls(self.base_tds_url, self.services)

class CatalogRef():
    def __init__(self, elementNode):
        self.name = elementNode.attrib["name"]
        self.href = elementNode.attrib["{http://www.w3.org/1999/xlink}href"]
        if self.href[0] == '/':
            self.href = self.href[1:]
        self.title = elementNode.attrib["{http://www.w3.org/1999/xlink}title"]

class Dataset():
    def __init__(self, elementNode, catalogUrl = ""):
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
                print "Must pass along the catalog URL to resolve the latest.xml dataset!"

    def resolveUrl(self,catalogUrl):
            if catalogUrl != "":
                resolverBase = catalogUrl.split("catalog.xml")[0]
                resolverUrl = resolverBase + self.urlPath
                resolverXml = basic_http_request(resolverUrl, return_response = True)
                tree = ET.parse(resolverXml)
                root = tree.getroot()
                self.catalog_name = root.attrib["name"]
                found = False
                for child in root.iter():
                    if not found:
                        tagType = child.tag.split('}')[-1]
                        if tagType == "dataset":
                            if child.attrib.has_key("urlPath"):
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
                accessUrls[service.serviceType] = serverUrl + service.base + self.urlPath

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

def basic_http_request(full_url, return_response = False):
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

