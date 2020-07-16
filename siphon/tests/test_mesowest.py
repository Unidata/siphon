# Copyright (c) 2017 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test University of Utah's MesoWest dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal
import pytest

from siphon.simplewebservice.mesowest import MesoWest
from siphon.testing import get_recorder


recorder = get_recorder(__file__)

@recorder.use_cassette('mesowest_data')
def test_mesowest():
    """Test that we are properly parsing data from the MesoWest archive."""
    df = MesoWest.request_data(datetime(2020, 7, 13), 'KONM')

    assert(df['time(mdt)'][0] == datetime(2020, 7, 13, 23, 55, 00).time())

    assert_almost_equal(df['temperature'][5],88.0,2)
    assert_almost_equal(df['dew_point'][5], 33.6, 2)
    assert_almost_equal(df['wet_bulb_temperature'][5], 57.3, 2)
    assert_almost_equal(df['relative_humidity'][5], 14.0, 2)
    assert_almost_equal(df['wind_speed'][5], 0, 2)
    assert_almost_equal(df['pressure'][5], 25.18, 2)
    assert_almost_equal(df['sea_level_pressure'][5], 29.6, 2)
    assert_almost_equal(df['altimeter'][5], 30.05, 2)
    assert_almost_equal(df['1500_m_pressure'][5], 25.07, 2)
    assert_almost_equal(df['visibility'][5], 10.0, 2)
