# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Tools for accessing atmospheric and oceanic science data on remote servers."""

# Version import needs to come first so everyone else can pull on import
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

__all__ = ['catalog', 'testing', 'http_util']
