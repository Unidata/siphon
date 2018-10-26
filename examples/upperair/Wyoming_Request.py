# Copyright (c) 2017 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
Wyoming Upper Air Data Request
==============================

This example shows how to use siphon's `simplewebswervice` support to create a query to
the Wyoming upper air archive.
"""

from datetime import datetime

from metpy.units import units

from siphon.simplewebservice.wyoming import WyomingUpperAir

####################################################
# Create a datetime object for the sounding and string of the station identifier.
date = datetime(2017, 9, 10, 6)
station = 'MFL'

####################################################
# Make the request (a pandas dataframe is returned).
df = WyomingUpperAir.request_data(date, station)

####################################################
# Inspect data columns in the dataframe.
print(df.columns)

####################################################
# Pull out a specific column of data.
print(df['pressure'])

####################################################
# Units are stored in a dictionary with the variable name as the key in the `units` attribute
# of the dataframe.
print(df.units)

####################################################
print(df.units['pressure'])

####################################################
# Units can then be attached to the values from the dataframe.
pressure = df['pressure'].values * units(df.units['pressure'])
temperature = df['temperature'].values * units(df.units['temperature'])
dewpoint = df['dewpoint'].values * units(df.units['dewpoint'])
u_wind = df['u_wind'].values * units(df.units['u_wind'])
v_wind = df['v_wind'].values * units(df.units['v_wind'])
