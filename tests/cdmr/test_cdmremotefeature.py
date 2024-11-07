# Copyright (c) 2014-2016 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test support for CDMRemoteFeature protocol."""

from datetime import datetime

import pytest

from siphon.cdmr.cdmremotefeature import CDMRemoteFeature
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@pytest.fixture
@recorder.use_cassette('cdmrf_header')
def cdmrf():
    """Set up all tests to point to the same dataset."""
    return CDMRemoteFeature('http://localhost:8080/thredds/cdmrfeature/grid/'
                            'test/HRRR_CONUS_2p5km_20160309_1600.grib2')


@recorder.use_cassette('cdmrf_feature_type')
def test_feature_type(cdmrf):
    """Test getting feature type from CDMRemoteFeature."""
    s = cdmrf.fetch_feature_type()
    assert s == b'GRID'


@recorder.use_cassette('cdmrf_data')
def test_data(cdmrf):
    """Test getting data from CDMRemoteFeature."""
    q = cdmrf.query()
    q.variables('Wind_speed_height_above_ground_1_Hour_Maximum')
    q.time(datetime(2016, 3, 9, 16))
    q.lonlat_box(-106, -105, 39, 40)
    s = cdmrf.get_data(q)
    assert s


@recorder.use_cassette('cdmrf_coords')
def test_coords(cdmrf):
    """Test getting coordinate data for CDMRemoteFeature."""
    q = cdmrf.query()
    q.variables('x')
    d = cdmrf.fetch_coords(q)
    assert d
