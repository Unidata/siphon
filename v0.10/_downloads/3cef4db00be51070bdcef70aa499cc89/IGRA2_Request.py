# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
IGRA2 Upper Air Data Request
==============================

This example shows how to use siphon's `simplewebswervice` support to create a
query to the Integrated Global Radiosonde Archive version 2.
"""

from datetime import datetime

from siphon.simplewebservice.igra2 import IGRAUpperAir

####################################################
# Create a datetime object for the sounding and string of the station identifier.
date = datetime(2014, 9, 10, 0)
station = 'USM00070026'

####################################################
# Make the request. IGRAUpperAir returns a dataframe containing the sounding data and
# a dataframe with station metadata from the sounding header.
df, header = IGRAUpperAir.request_data(date, station)

####################################################
# Inspect data columns in the dataframe.
print(df.columns)

# Inspect metadata from the data headers
print(header.columns)

####################################################
# Pull out a specific column of data.
print(df['pressure'])
print(header['latitude'])

####################################################
# Units are stored in a dictionary with the variable name as the key in the `units`
# attribute of the dataframe.
print(df.units)
print(header.units)

####################################################
print(df.units['pressure'])

####################################################
# Multiple records can be extracted simultaneously:
date = [datetime(2014, 9, 10, 0), datetime(2015, 9, 10, 12)]
station = 'USM00070026'
df, header = IGRAUpperAir.request_data(date, station)

print(df.head())
print(header.head())

####################################################
# IGRA2-Derived data can be accessed using the keyword derived=True.
# This data has much more information in the headers.
df, header = IGRAUpperAir.request_data(date, station, derived=True)

####################################################
# Inspect data columns in the dataframe.
print(df.columns)
print(header.columns)
