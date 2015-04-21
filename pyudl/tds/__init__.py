from . import catalog_util
from .catalog_util import *  # noqa
from .TDSCatalog import TDSCatalog, get_latest_access_url

__all__ = ['TDSCatalog', 'get_latest_access_url']
__all__.extend(catalog_util.__all__)

del catalog_util

#
# This will pull in and expose the functions defined in the __all__
#   list variable in catalog_util.py, and overall will work like this:
#
#    import pyudl
#    dataset_url = "url goes here"
#    access_url = pyudl.tds.get_latest_dods_url(dataset_url)
#
