# Version import needs to come first so everyone else can pull on import
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

from . import cdmr  # noqa
__all__ = ['catalog', 'cdmr']
