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
from __future__ import print_function

from siphon.catalog import TDSCatalog

###########################################
cat = TDSCatalog('http://thredds.ucar.edu/thredds/catalog.xml')
print(list(cat.catalog_refs))
