# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
===============================
Multi Station Calls and Mapping
===============================

In this example we will be using Siphon's simplewebservice support to query
ACIS Web Services for multiple stations. We will plot precipitation
values recorded in Colorado and Wyoming during the 2013 flooding event.
"""

import cartopy.crs as ccrs
import cartopy.feature as feat
import matplotlib.pyplot as plt

from siphon.simplewebservice.acis import acis_request

###########################################
# First, we need to assemble a dictionary containing the information we want.
# In this example we want multiple station information, which indicates we
# need a MultiStnData call. Our event period spans from September 9 through
# September 12, 2013. We know we are interested in precipitation totals,
# but we are also going to take advantage of the long-term record in ACIS
# and ask it to return what the departure from normal precipitation was on
# this day.

parameters = {'state': 'co', 'sdate': '20130909', 'edate': '20130912', 'elems': [
    {'name': 'pcpn', 'interval': 'dly'},
    {'name': 'pcpn', 'interval': 'dly', 'normal': 'departure'}]}

method = 'MultiStnData'
###########################################
# In this case, rather than using station ID's, we are able to specify a new
# parameter called 'state'. If we were interested in other states, we could just
# add another to the list like this: 'co,wy'. Also notice how we are getting
# both the precipitation and departure from normal within one variable. We'll
# see how this changes the final data dictionary. Now let's make our call and
# review our data.

my_data = acis_request(method, parameters)

print(my_data)

###########################################
# MultiStnData calls take longer to return than single stations, especially when
# you request multiple states. We can see the data is divided by station, with
# each station having it's own meta and data components. This time we also have
# multiple values in each data list. Each value corresponds to the variable we
# requested, in the order we requested it. So in this case, we have the
# precipitation value, followed by the departure from normal value. Before we
# plot this information, we need to add up the precipitation sums. But rather
# than doing it in Python, let's make another ACIS call that prepares this for
# us.

parameters = {'state': 'co', 'sdate': '20130909', 'edate': '20130912', 'elems': [
    {'name': 'pcpn', 'interval': 'dly', 'smry': 'sum', 'smry_only': 1},
    {'name': 'pcpn', 'interval': 'dly', 'smry': 'sum', 'smry_only': 1, 'normal': 'departure'}]}

my_data = acis_request(method, parameters)

print(my_data)

###########################################
# First of all, we have two new components to our elements: 'smry' and 'smry_only'.
# 'smry' allows us to summarize the data over our time period. There are a few
# options for this, including being able to count the number of records exceeding
# a threshold (something we will explore in the next example). The other parameter,
# 'smry_only', allows us to only return the summary value and not the intermediate
# data.
#
# Now let's look at how our data has changed. Rather than having a just a 'meta'
# and 'data' component, we have a new one called 'smry'. As you've guessed,
# this contains our summary information (also in the order we requested it).
# By specifying 'smry_only', there is no 'data' component. If we also wanted
# all 4 days of data, we would simply remove that parameter.
#
# To wrap up this example, we will finally plot our precipitation sums and
# departures onto a map using CartoPy. To do this we will utilize
# the meta data that is provided with each station's data. Within the metadata
# is a 'll' element that contains the latitude and longitude, which is perfect
# for plotting!
#
# One final thing to note is that not all stations have location information.
# Stations from the ThreadEx network cover general areas, and thus aren't
# packaged with precise latitudes and longitudes. We will skip them by
# identifying their network ID of 9 in the ACIS metadata. Don't worry about
# lost information though! These summarize stations that already exist within
# their areas!

lat = []
lon = []
pcpn = []
pcpn_dep = []

for stn in my_data['data']:
    # Skip threaded stations! They have no lat/lons
    if stn['meta']['sids'][-1].endswith('9'):
        continue
    # Skip stations with missing or trace data
    if stn['smry'][0] in ['M', 'T'] or stn['smry'][1] in ['M', 'T']:
        continue

    lat.append(stn['meta']['ll'][1])
    lon.append(stn['meta']['ll'][0])
    pcpn.append(float(stn['smry'][0]))
    pcpn_dep.append(float(stn['smry'][1]))
###########################################
# Now we setup our map and plot the data! We are going to plot the station
# locations with a '+' symbol and label them with the precipitation value.
# We will use the departures to set the departure from normal values where:
# * Departure < 0 is Red
# * Departure > 0 is Green
# * Departure > 2 is Magenta
#
# This should help us visualize where the precipitation event was strongest!

proj = ccrs.LambertConformal(central_longitude=-105, central_latitude=0,
                             standard_parallels=[35])

fig = plt.figure(figsize=(20, 10))
ax = fig.add_subplot(1, 1, 1, projection=proj)

ax.add_feature(feat.LAND, zorder=-1)
ax.add_feature(feat.OCEAN, zorder=-1)
ax.add_feature(feat.LAKES, zorder=-1)
ax.coastlines(resolution='110m', zorder=2, color='black')
ax.add_feature(feat.STATES, edgecolor='black')
ax.add_feature(feat.BORDERS, linewidth=2, edgecolor='black')

# Set plot bounds
ax.set_extent((-109.9, -101.8, 36.5, 41.3))

# Plot each station, labeling based on departure
for stn in range(len(pcpn)):
    if pcpn_dep[stn] >= 0 and pcpn_dep[stn] < 2:
        ax.plot(lon[stn], lat[stn], 'g+', markersize=7, transform=ccrs.Geodetic())
        ax.text(lon[stn], lat[stn], pcpn[stn], transform=ccrs.Geodetic())
    elif pcpn_dep[stn] >= 2:
        ax.plot(lon[stn], lat[stn], 'm+', markersize=7, transform=ccrs.Geodetic())
        ax.text(lon[stn], lat[stn], pcpn[stn], transform=ccrs.Geodetic())
    elif pcpn_dep[stn] < 0:
        ax.plot(lon[stn], lat[stn], 'r+', markersize=7, transform=ccrs.Geodetic())
        ax.text(lon[stn], lat[stn], pcpn[stn], transform=ccrs.Geodetic())
ax.plot(pcpn)

plt.show()
