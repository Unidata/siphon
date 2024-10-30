# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
===============
THREDDS Catalog
===============

Read a catalog from THREDDS Data Server.

This example grabs a remote catalog and prints out the catalog references
contained within.
"""

# This is currently a placeholder for a better example
from siphon.catalog import TDSCatalog
from siphon.http_util import session_manager

###########################################
cat = TDSCatalog('http://thredds.ucar.edu/thredds/catalog.xml')
print(list(cat.catalog_refs))

###########################################
# Basic HTTP authentication can also be used by using the HTTP session manager
# and setting some default options for HTTP sessions
session_manager.set_session_options(auth=('username', 'password'))
cat = TDSCatalog('https://thredds.rda.ucar.edu/thredds/catalog/catalog.xml')
