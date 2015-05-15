# use __init__.py to setup the namespace
from . import tds
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

__all__ = ['tds']
