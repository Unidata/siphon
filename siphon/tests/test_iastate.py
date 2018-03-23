# Copyright (c) 2017 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test Iowa State upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal

from siphon.simplewebservice.iastate import IAStateUpperAir
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


@recorder.use_cassette('iastate_sounding')
def test_iastate():
    """Test that we are properly parsing data from the Iowa State archive."""
    df = IAStateUpperAir.request_data(datetime(1999, 5, 4, 0), 'OUN')

    assert_almost_equal(df['pressure'][6], 872.7, 2)
    assert_almost_equal(df['height'][6], 1172.0, 2)
    assert_almost_equal(df['temperature'][6], 18.2, 2)
    assert_almost_equal(df['dewpoint'][6], 15.1, 2)
    assert_almost_equal(df['u_wind'][6], 4.631, 2)
    assert_almost_equal(df['v_wind'][6], 37.716, 2)
    assert_almost_equal(df['speed'][6], 38.0, 1)
    assert_almost_equal(df['direction'][6], 187.0, 1)

    assert(df.units['pressure'] == 'hPa')
    assert(df.units['height'] == 'meter')
    assert(df.units['temperature'] == 'degC')
    assert(df.units['dewpoint'] == 'degC')
    assert(df.units['u_wind'] == 'knot')
    assert(df.units['v_wind'] == 'knot')
    assert(df.units['speed'] == 'knot')
    assert(df.units['direction'] == 'degrees')


@recorder.use_cassette('iastate_high_alt_sounding')
def test_high_alt_iastate():
    """Test Iowa State data that starts at pressure less than 925 hPa."""
    df = IAStateUpperAir.request_data(datetime(2010, 12, 9, 12), 'BOI')

    assert_almost_equal(df['pressure'][0], 919.0, 2)
    assert_almost_equal(df['height'][0], 871.0, 2)
    assert_almost_equal(df['temperature'][0], -0.1, 2)
    assert_almost_equal(df['dewpoint'][0], -0.2, 2)
    assert_almost_equal(df['u_wind'][0], 2.598, 2)
    assert_almost_equal(df['v_wind'][0], 1.500, 2)
    assert_almost_equal(df['speed'][0], 3.0, 1)
    assert_almost_equal(df['direction'][0], 240.0, 1)
