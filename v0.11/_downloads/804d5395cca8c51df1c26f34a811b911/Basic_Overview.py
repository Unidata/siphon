# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
=============================
Basic ACIS Web Services Usage
=============================

Siphon's simplewebservice support also includes the ability to query the
Regional Climate Centers' ACIS data servers. ACIS data provides daily records
for most station networks in the U.S. and is updated hourly.

In this example we will be querying the service for 20 years of temperature data
from Denver International Airport.
"""

import matplotlib.pyplot as plt

from siphon.simplewebservice.acis import acis_request

###########################################
# First, we need to assemble a dictionary containing the information we want.
# For this example we want the average temperature at Denver International (KDEN)
# from January 1, 1997 to December 1, 2017. While we could get the daily data,
# we will instead request the monthly averages, which the remote service will
# find for us.
parameters = {'sid': 'KDEN', 'sdate': '19970101', 'edate': '20171231', 'elems': [
    {'name': 'avgt', 'interval': 'mly', 'duration': 'mly', 'reduce': 'mean'}]}

###########################################
# These parameters are used to specify what kind of data we want. We are
# formatting this as a dictionary, the acis_request function will handle the
# conversion of this into a JSON string for us!
#
# As we explain how this dictionary is formatted, feel free to follow along
# using the API documentation here :http://www.rcc-acis.org/docs_webservices.html
#
# The first section of the parameters dictionary is focused on the station and
# period of interest. We have a 'sid' element where the airport identifier is,
# and sdate/edate which correspond to the starting and ending dates of the
# period of interest.
#
# The 'elems' list contains individual dictionaries of elements (variables) of
# interest. In this example we are requesting the average monthly temperature.
# If we also wanted the minimum temperature, we would simply add an additional
# dictionary to the 'elems' list.
#
# Now that we have assembled our dictionary, we need to decide what type of
# request we are making. You can request meta data (information about the
# station), station data (data from an individual station), data from multiple
# stations, or even images of pre-prepared data.
#
# In this case we are interested in a single station, so we will be using the
# method set aside for this called, 'StnData'.

method = 'StnData'

###########################################
# Now that we have our request information ready, we can call the acis_request
# function and receive our data!

my_data = acis_request(method, parameters)

###########################################
# The data is also returned in a dictionary format, decoded from a JSON string.

print(my_data)

###########################################
# We can see there are two parts to this data: The metadata, and the data. The
# metadata can be useful in mapping the observations (We'll do this in a later
# example).
#
# To wrap this example up, we are going to do a simple line graph of this 30
# year temperature data using MatPlotLib! Notice that the data is decoded as
# a string, so you should convert those back into numbers before use.
#
# * Note: Missing data is recorded as M!

stn_name = my_data['meta']['name']

avgt = []
dates = []
for obs in my_data['data']:
    if obs[0].endswith('01'):
        dates.append(obs[0])
    else:
        dates.append('')
    avgt.append(float(obs[1]))

X = list(range(len(avgt)))

plt.title(stn_name)
plt.ylabel('Average Temperature (F)')
plt.plot(X, avgt)
plt.xticks(X, dates, rotation=45)

plt.show()
