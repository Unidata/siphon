# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""
=======================
TDS Radar Query Service
=======================

Use Siphon to get NEXRAD Level 3 data from a TDS.
"""
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import numpy as np

from siphon.cdmr import Dataset
from siphon.radarserver import get_radarserver_datasets, RadarServer

###########################################
# First, point to the top-level thredds radar server accessor to find what datasets are
# available.
ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
print(list(ds))

###########################################
# Now create an instance of RadarServer to point to the appropriate
# radar server access URL. This is pulled from the catalog reference url.
url = ds['NEXRAD Level III Radar from IDD'].follow().catalog_url
rs = RadarServer(url)

###########################################
# Look at the variables available in this dataset
print(rs.variables)

###########################################
# Create a new query object to help request the data. Using the chaining
# methods, ask for data from radar CYS (Cheyenne) for now for the product
# N0B, which is reflectivity data for the lowest tilt. We see that when the query
# is represented as a string, it shows the encoded URL.
query = rs.query()
query.stations('CYS').time(datetime.now(timezone.utc)).variables('N0B')

###########################################
# We can use the RadarServer instance to check our query, to make
# sure we have required parameters and that we have chosen valid
# station(s) and variable(s)
rs.validate_query(query)

###########################################
# Make the request, which returns an instance of TDSCatalog. This
# handles parsing the catalog
catalog = rs.get_catalog(query)

###########################################
# We can look at the datasets on the catalog to see what data we found by the query. We
# find one NIDS file in the return.
print(catalog.datasets)

###########################################
# We can pull that dataset out of the dictionary and look at the available access URLs.
# We see URLs for OPeNDAP, CDMRemote, and HTTPServer (direct download).
ds = list(catalog.datasets.values())[0]
print(ds.access_urls)

###########################################
# We'll use the CDMRemote reader in Siphon and pass it the appropriate access URL.
data = Dataset(ds.access_urls['CdmRemote'])

###########################################
# The CDMRemote reader provides an interface that is almost identical to the usual python
# NetCDF interface. We pull out the variables we need for azimuth and range, as well as
# the data itself.
rng = data.variables['gate'][:] / 1000.
az = data.variables['azimuth'][:]
ref = data.variables['BaseReflectivityDR'][:]

###########################################
# Need to adjust range and azimuth so that they bound the range gates rather than having
# a single point at the start of the gate.
rng = np.append(rng, rng[-1] - rng[-2])
diff = np.diff(az)
diff[diff > 180] -= 360.
diff[diff < -180] += 360.
avg_spacing = diff.mean()
az = np.append(az, az[-1] + avg_spacing)

###########################################
# Then convert the polar coordinates to Cartesian
x = rng * np.sin(np.deg2rad(az))[:, None]
y = rng * np.cos(np.deg2rad(az))[:, None]
ref = np.ma.array(ref, mask=np.isnan(ref))

###########################################
# Finally, we plot them up using matplotlib.
fig, ax = plt.subplots(1, 1, figsize=(9, 8))
ax.pcolormesh(x, y, ref)
ax.set_aspect('equal', 'datalim')
ax.set_xlim(-460, 460)
ax.set_ylim(-460, 460)
plt.show()
