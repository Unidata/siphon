# Copyright (c) 2014-2016 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test interaction with xarray library."""

from numpy.testing import assert_almost_equal
import pytest

from siphon.testing import get_recorder

recorder = get_recorder(__file__)
xarray = pytest.importorskip('xarray')


@recorder.use_cassette('rap_compressed')
def test_xarray_dataset():
    """Test getting data using xarray open_dataset over CDMRemote."""
    from siphon.cdmr.xarray_support import CDMRemoteStore

    store = CDMRemoteStore('http://thredds-dev.unidata.ucar.edu/thredds/cdmremote/'
                           'grib/NCEP/RAP/CONUS_13km/RR_CONUS_13km_20150518_1200.grib2/GC')
    ds = xarray.open_dataset(store)
    assert 'Temperature_isobaric' in ds
    subset = ds['Temperature_isobaric'][0, 0] * 1  # Doing math forces data request
    assert_almost_equal(subset[0, 0].values, 206.65640259, 6)
