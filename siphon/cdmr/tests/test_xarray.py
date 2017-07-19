# Copyright (c) 2014-2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test interaction with xarray library."""

from numpy.testing import assert_almost_equal
from xarray import open_dataset

from siphon.cdmr.xarray_support import CDMRemoteStore
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@recorder.use_cassette('rap_compressed')
def test_xarray_dataset():
    """Test getting data using xarray open_dataset over CDMRemote."""
    store = CDMRemoteStore('http://thredds-dev.unidata.ucar.edu/thredds/cdmremote/'
                           'grib/NCEP/RAP/CONUS_13km/RR_CONUS_13km_20150518_1200.grib2/GC')
    ds = open_dataset(store)
    assert 'Temperature_isobaric' in ds
    subset = ds['Temperature_isobaric'][0, 0] * 1  # Doing math forces data request
    assert_almost_equal(subset[0, 0].values, 206.65640259, 6)
