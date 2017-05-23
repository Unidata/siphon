# Copyright (c) 2014-2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test support for CDMRemoteFeature protocol."""

from datetime import datetime

from siphon.cdmr.cdmremotefeature import CDMRemoteFeature
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


class TestCDMRemoteFeature(object):
    """Test the CDMRemoteFeature HTTP interface."""

    @recorder.use_cassette('cdmrf_header')
    def setup(self):
        """Set up all tests to point to the same dataset."""
        self.cdmrf = CDMRemoteFeature('http://localhost:8080/thredds/cdmrfeature/grid/'
                                      'test/HRRR_CONUS_2p5km_20160309_1600.grib2')

    @recorder.use_cassette('cdmrf_feature_type')
    def test_feature_type(self):
        """Test getting feature type from CDMRemoteFeature."""
        s = self.cdmrf.fetch_feature_type()
        assert s == b'GRID'

    @recorder.use_cassette('cdmrf_data')
    def test_data(self):
        """Test getting data from CDMRemoteFeature."""
        q = self.cdmrf.query()
        q.variables('Wind_speed_height_above_ground_1_Hour_Maximum')
        q.time(datetime(2016, 3, 9, 16))
        q.lonlat_box(-106, -105, 39, 40)
        s = self.cdmrf.get_data(q)
        assert s

    @recorder.use_cassette('cdmrf_coords')
    def test_coords(self):
        """Test getting coordinate data for CDMRemoteFeature."""
        q = self.cdmrf.query()
        q.variables('x')
        d = self.cdmrf.fetch_coords(q)
        assert d
