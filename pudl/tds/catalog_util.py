import xml.etree.ElementTree as ET
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

# add function names to __all__ in order to expose them in the
# pudl.tds namespace
__all__ = ["get_latest_dods_url",
           "get_service_endpoint",
           "get_resolver_xml_url",
           "find_dataset",
           "get_element_root_from_url",
           "get_url_path"]


xmlns_prefix = ("{http://www.unidata.ucar.edu/namespaces/thredds"
                "/InvCatalog/v1.0}")


def get_url_path(url):
    """Return a URL with path only (no file name)"""
    o = urlparse(url)
    parts = o.path.split('/')
    return o.scheme + "://" + o.netloc + '/'.join(parts[:-1])


def get_element_root_from_url(url):
    """Given a XML URL, return an element root"""
    data = urlopen(url)
    root = ET.parse(data).getroot()
    data.close()
    return root


def find_dataset(root, service_name):
    """
    Given an  element root, and  a service name, recursively  find the
    first dataset with that service name
    """
    for ds in root.findall(xmlns_prefix + 'dataset'):
        sn = ds.find(xmlns_prefix + "serviceName")
        if ((sn is not None) and (service_name == sn.text)):
            return ds
        else:
            if find_dataset(ds, service_name) is not None:
                return find_dataset(ds, service_name)


def get_resolver_xml_url(dataset_url):
    """Given a dataset URL, return the resolver XML URL."""
    root = get_element_root_from_url(dataset_url)
    latest = ''
    latest_base = ''
    latest_url = None
    for s in root.findall(xmlns_prefix + 'service'):
        if (s.get("serviceType") == "Resolver"):
            latest = s.get("name")
            latest_base = s.get("base")
    ds = find_dataset(root, latest)
    if (ds is not None):
        # TODO: generalize this to handle relatives paths starting with a '/'
        latest_url = get_url_path(
            dataset_url) + latest_base + '/' + ds.get('urlPath')
    return latest_url


def get_service_endpoint(root, service):
    """
    Given an element root and a service, return the end point relative path.
    """
    # TODO: Deal with suffix
    service_dict = {}
    for s in root.findall(xmlns_prefix + 'service'):
        if (s.get("serviceType") == "Compound"):
            for child in s:
                service_dict[child.get("serviceType")] = child.get("base")
    return service_dict[service]


def get_latest_dods_url(dataset_url):
    """Given a top level THREDDS dataset URI, return the latest dataset."""
    o = urlparse(dataset_url)
    resolver = get_resolver_xml_url(dataset_url)
    latest = None
    if (resolver is not None):
        root = get_element_root_from_url(resolver)
        ds = root.find(xmlns_prefix + 'dataset')
        latest = o.scheme + "://" + o.netloc + \
            get_service_endpoint(root, 'OPENDAP') + ds.get('urlPath')
    return latest
