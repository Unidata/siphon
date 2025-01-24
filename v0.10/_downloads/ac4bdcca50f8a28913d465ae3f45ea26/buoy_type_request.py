# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
NDBC Buoy Data Request (of any type)
====================================

The NDBC keeps a 40-day recent rolling file for each buoy. This examples shows how to access
the other types of data available for a buoy.
"""

from siphon.simplewebservice.ndbc import NDBC

####################################################
# Request the types of data available from a given buoy.
data_aval = NDBC.buoy_data_types('42001')
print(data_aval)

####################################################
# Get a pandas data frame of all of the observations, meteorological data is the default
# observation set to query.
df = NDBC.realtime_observations('42001', data_type='supl')
df.head()
