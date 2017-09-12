# Copyright (c) 2017 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test Wyoming upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal

from siphon.simplewebservice.wyoming import WyomingUpperAir
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


@recorder.use_cassette('wyoming_sounding')
def test_wyoming():
    """Test that we are properly parsing data from the wyoming archive."""
    df = WyomingUpperAir.request_data(datetime(1999, 5, 4, 0), 'OUN')

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


@recorder.use_cassette('wyoming_high_alt_sounding')
def test_high_alt_wyoming():
    """Test Wyoming data that starts at pressure less than 925 hPa."""
    df = WyomingUpperAir.request_data(datetime(2010, 12, 9, 12), 'BOI')

    assert_almost_equal(df['pressure'][2], 890.0, 2)
    assert_almost_equal(df['height'][2], 1133., 2)
    assert_almost_equal(df['temperature'][2], 5.4, 2)
    assert_almost_equal(df['dewpoint'][2], 3.9, 2)
    assert_almost_equal(df['u_wind'][2], -0.42, 2)
    assert_almost_equal(df['v_wind'][2], 5.99, 2)
