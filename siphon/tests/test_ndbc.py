# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test National Data Buoy Center (NDBC) dataset access."""

from datetime import datetime

import numpy as np
from numpy.testing import assert_almost_equal, assert_equal
import pytest

from siphon.simplewebservice.ndbc import NDBC
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


@recorder.use_cassette('ndbc_latest')
def test_ndbc_latest():
    """Test that we are properly parsing latest NDBC observations."""
    #truth = ['41004', 32.501, -79.09899999999999, 190.0, 6.0, 7.0, 1.2,
    #         5.0, 4.8, 186.0, 1016.5, np.nan, 28.0, 28.7, 25.9,
    #         np.nan, np.nan, Timestamp('2018-07-30 20:50:00')]
    #'station', 'latitude', 'longitude', 'wind_direction', 'wind_speed',
    #'wind_gust', 'wave_height', 'dominant_wave_period',
    #'average_wave_period', 'dominant_wave_direction', 'pressure',
    #'air_temperature', 'water_temperature', 'dewpoint', 'visibility',
    #'3hr_pressure_tendency', 'water_level_above_mean', 'time'



    #
    #['41004' 32.501 -79.09899999999999 200.0 5.0 7.0 nan nan nan nan 1016.9
    # nan 28.1 28.8 25.9 nan nan Timestamp('2018-07-30 21:10:00')]

    df = NDBC.latest_observations()

    assert(df['station'][10] == '41004')
    assert_almost_equal(df['latitude'][10], 32.501, 3)
    assert_almost_equal(df['longitude'][10], -79.0989, 3)

    assert_almost_equal(df['wind_direction'][10], 200.0, 1)
    assert_almost_equal(df['wind_speed'][10], 5.0, 1)
    assert_almost_equal(df['wind_gust'][10], 7.0, 1)
    assert_equal(df['wave_height'][10], np.nan)
    assert_equal(df['dominant_wave_period'][10], np.nan)
    assert_equal(df['average_wave_period'][10], np.nan)
    assert_equal(df['dominant_wave_direction'][10], np.nan)
    assert_almost_equal(df['pressure'][10], 1016.9, 1)
    assert_almost_equal(df['air_temperature'][10], 28.1, 1)
    assert_almost_equal(df['water_temperature'][10], 28.8, 1)
    assert_almost_equal(df['dewpoint'][10], 25.9, 1)
    assert_equal(df['visibility'][10], np.nan)
    assert_equal(df['3hr_pressure_tendency'][10], np.nan)
    assert_equal(df['water_level_above_mean'][10], np.nan)
    assert_equal(df['time'][10], datetime(2018, 7, 30, 21, 10))

    assert(df.units['station'] is None)
    assert(df.units['latitude'] == 'degrees')
    assert(df.units['longitude'] == 'degrees')
    assert(df.units['wind_direction'] == 'degrees')
    assert(df.units['wind_speed'] == 'meters/second')
    assert(df.units['wind_gust'] == 'meters/second')
    assert(df.units['wave_height'] == 'meters')
    assert(df.units['dominant_wave_period'] == 'seconds')
    assert(df.units['average_wave_period'] == 'seconds')
    assert(df.units['dominant_wave_direction'] == 'degrees')
    assert(df.units['pressure'] == 'hPa')
    assert(df.units['air_temperature'] == 'degC')
    assert(df.units['water_temperature'] == 'degC')
    assert(df.units['dewpoint'] == 'degC')
    assert(df.units['visibility'] == 'nautical_mile')
    assert(df.units['3hr_pressure_tendency'] == 'hPa')
    assert(df.units['water_level_above_mean'] == 'feet')
    assert(df.units['time'] is None)
