# coding: utf-8

# # This is currently a placeholder for a better example
from __future__ import print_function
from siphon.catalog import TDSCatalog

cat = TDSCatalog('http://thredds.ucar.edu/thredds/catalog.xml')

print(list(cat.catalog_refs.keys()))

