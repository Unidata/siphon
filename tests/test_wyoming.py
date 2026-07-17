# Copyright (c) 2017 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test Wyoming upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal
import pandas as pd
import pytest

from siphon.simplewebservice.wyoming import WyomingUpperAir
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@pytest.mark.parametrize('recalc', [True, False])
def test_wyoming(recalc):
    """Test that we are properly parsing data from the Wyoming archive."""
    cassette = 'wyoming_sounding_recalculate' if recalc else 'wyoming_sounding'
    with recorder.use_cassette(cassette):
        df = WyomingUpperAir.request_data(datetime(1999, 5, 4, 0), 'OUN', recalc=recalc)

    assert df['time'][0] == datetime(1999, 5, 3, 23, 2)
    assert df['station'][0] == 'OUN'
    assert df['latitude'][0] == 35.18
    assert df['longitude'][0] == -97.44

    assert_almost_equal(df['pressure'][5], 867.8, 2)
    assert_almost_equal(df['height'][5], 1219., 2)
    assert_almost_equal(df['height'][30], 10505., 2)
    assert_almost_equal(df['temperature'][5], 17.4, 2)
    assert_almost_equal(df['dewpoint'][5], 14.4, 2)
    assert_almost_equal(df['u_wind'][5], 3.403, 2)
    assert_almost_equal(df['v_wind'][5], 19.30, 2)
    assert_almost_equal(df['speed'][5], 19.6, 1)
    assert_almost_equal(df['direction'][5], 190.0, 1)

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'm/s'
    assert df.units['v_wind'] == 'm/s'
    assert df.units['speed'] == 'm/s'
    assert df.units['direction'] == 'degrees'
    assert df.units['latitude'] == 'degrees'
    assert df.units['longitude'] == 'degrees'
    assert df.units['station'] is None
    assert df.units['time'] is None


@recorder.use_cassette('wyoming_high_alt_sounding')
def test_high_alt_wyoming():
    """Test Wyoming data that starts at pressure less than 925 hPa."""
    df = WyomingUpperAir.request_data(datetime(2010, 12, 9, 12), 'BOI')

    assert df['time'][0] == datetime(2010, 12, 9, 11, 6)
    assert df['station'][0] == 'BOI'
    assert df['latitude'][0] == 43.56
    assert df['longitude'][0] == -116.21

    assert_almost_equal(df['pressure'][2], 890.0, 2)
    assert_almost_equal(df['height'][2], 1133., 2)
    assert_almost_equal(df['temperature'][2], 5.4, 2)
    assert_almost_equal(df['dewpoint'][2], 3.9, 2)
    assert_almost_equal(df['u_wind'][2], -0.216, 2)
    assert_almost_equal(df['v_wind'][2], 3.09, 2)
    assert_almost_equal(df['speed'][2], 3.1, 1)
    assert_almost_equal(df['direction'][2], 176.0, 1)

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'm/s'
    assert df.units['v_wind'] == 'm/s'
    assert df.units['speed'] == 'm/s'
    assert df.units['direction'] == 'degrees'
    assert df.units['latitude'] == 'degrees'
    assert df.units['longitude'] == 'degrees'
    assert df.units['station'] is None
    assert df.units['time'] is None


@recorder.use_cassette('wyoming_no_data')
def test_no_data_wyoming():
    """Test Wyoming data when no data are available."""
    with pytest.raises(ValueError):
        WyomingUpperAir.request_data(datetime(2010, 12, 9, 1), 'BOI')


@recorder.use_cassette('wyoming_sounding_heights')
def test_wyoming_heights():
    """Test that we are properly parsing height data from the Wyoming archive."""
    df = WyomingUpperAir.request_data(datetime(2023, 5, 22, 12), 'OUN')

    assert_almost_equal(df['height'][140], 10336.0, 2)
    assert_almost_equal(df['direction'][1], 145.0, 1)


# GH #749
@recorder.use_cassette('wyoming_missing_station_info')
def test_missing_station():
    """Test that we can still return data for stations missing from the Wyoming archive."""
    df = WyomingUpperAir.request_data(datetime(2012, 1, 1, 0),  '82244')
    assert df['station'][0] == '82244'
    assert all(pd.isna(df['latitude']))
    assert all(pd.isna(df['longitude']))
