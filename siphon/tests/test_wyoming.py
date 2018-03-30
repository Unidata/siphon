# Copyright (c) 2017 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test Wyoming upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal
import pytest

from siphon.simplewebservice.wyoming import WyomingUpperAir
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


@recorder.use_cassette('wyoming_sounding')
def test_wyoming():
    """Test that we are properly parsing data from the Wyoming archive."""
    df = WyomingUpperAir.request_data(datetime(1999, 5, 4, 0), 'OUN')

    assert(df['time'][0] == datetime(1999, 5, 4, 0))
    assert(df['station'][0] == 'OUN')
    assert(df['station_number'][0] == 72357)
    assert(df['latitude'][0] == 35.18)
    assert(df['longitude'][0] == -97.44)
    assert(df['elevation'][0] == 345.0)

    assert_almost_equal(df['pressure'][5], 867.9, 2)
    assert_almost_equal(df['height'][5], 1219., 2)
    assert_almost_equal(df['temperature'][5], 17.4, 2)
    assert_almost_equal(df['dewpoint'][5], 14.3, 2)
    assert_almost_equal(df['u_wind'][5], 6.60, 2)
    assert_almost_equal(df['v_wind'][5], 37.42, 2)
    assert_almost_equal(df['speed'][5], 38.0, 1)
    assert_almost_equal(df['direction'][5], 190.0, 1)

    assert(df.units['pressure'] == 'hPa')
    assert(df.units['height'] == 'meter')
    assert(df.units['temperature'] == 'degC')
    assert(df.units['dewpoint'] == 'degC')
    assert(df.units['u_wind'] == 'knot')
    assert(df.units['v_wind'] == 'knot')
    assert(df.units['speed'] == 'knot')
    assert(df.units['direction'] == 'degrees')
    assert(df.units['latitude'] == 'degrees')
    assert(df.units['longitude'] == 'degrees')
    assert(df.units['elevation'] == 'meter')
    assert(df.units['station'] is None)
    assert(df.units['station_number'] is None)
    assert(df.units['time'] is None)


@recorder.use_cassette('wyoming_high_alt_sounding')
def test_high_alt_wyoming():
    """Test Wyoming data that starts at pressure less than 925 hPa."""
    df = WyomingUpperAir.request_data(datetime(2010, 12, 9, 12), 'BOI')

    assert(df['time'][0] == datetime(2010, 12, 9, 12))
    assert(df['station'][0] == 'BOI')
    assert(df['station_number'][0] == 72681)
    assert(df['latitude'][0] == 43.56)
    assert(df['longitude'][0] == -116.21)
    assert(df['elevation'][0] == 874.0)

    assert_almost_equal(df['pressure'][2], 890.0, 2)
    assert_almost_equal(df['height'][2], 1133., 2)
    assert_almost_equal(df['temperature'][2], 5.4, 2)
    assert_almost_equal(df['dewpoint'][2], 3.9, 2)
    assert_almost_equal(df['u_wind'][2], -0.42, 2)
    assert_almost_equal(df['v_wind'][2], 5.99, 2)
    assert_almost_equal(df['speed'][2], 6.0, 1)
    assert_almost_equal(df['direction'][2], 176.0, 1)

    assert(df.units['pressure'] == 'hPa')
    assert(df.units['height'] == 'meter')
    assert(df.units['temperature'] == 'degC')
    assert(df.units['dewpoint'] == 'degC')
    assert(df.units['u_wind'] == 'knot')
    assert(df.units['v_wind'] == 'knot')
    assert(df.units['speed'] == 'knot')
    assert(df.units['direction'] == 'degrees')
    assert(df.units['latitude'] == 'degrees')
    assert(df.units['longitude'] == 'degrees')
    assert(df.units['elevation'] == 'meter')
    assert(df.units['station'] is None)
    assert(df.units['station_number'] is None)
    assert(df.units['time'] is None)


@recorder.use_cassette('wyoming_no_data')
def test_no_data_wyoming():
    """Test Wyoming data when no data are available."""
    with pytest.raises(ValueError):
        WyomingUpperAir.request_data(datetime(2010, 12, 9, 1), 'BOI')
