# Copyright (c) 2017,2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test Iowa State upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal
import pytest

from siphon.simplewebservice.iastate import IAStateUpperAir
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@recorder.use_cassette('iastate_sounding')
def test_iastate():
    """Test that we are properly parsing data from the Iowa State archive."""
    df = IAStateUpperAir.request_data(datetime(1999, 5, 4, 0), 'OUN')

    assert df['time'][0] == datetime(1999, 5, 4, 0)
    assert df['station'][0] == 'KOUN'

    assert_almost_equal(df['pressure'][6], 872.7, 2)
    assert_almost_equal(df['height'][6], 1172.0, 2)
    assert_almost_equal(df['temperature'][6], 18.2, 2)
    assert_almost_equal(df['dewpoint'][6], 15.1, 2)
    assert_almost_equal(df['u_wind'][6], 4.631, 2)
    assert_almost_equal(df['v_wind'][6], 37.716, 2)
    assert_almost_equal(df['speed'][6], 38.0, 1)
    assert_almost_equal(df['direction'][6], 187.0, 1)

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'knot'
    assert df.units['v_wind'] == 'knot'
    assert df.units['speed'] == 'knot'
    assert df.units['direction'] == 'degrees'
    assert df.units['station'] is None
    assert df.units['time'] is None


@recorder.use_cassette('iastate_high_alt_sounding')
def test_high_alt_iastate():
    """Test Iowa State data that starts at pressure less than 925 hPa."""
    df = IAStateUpperAir.request_data(datetime(2010, 12, 9, 12), 'BOI')

    assert df['time'][0] == datetime(2010, 12, 9, 12)
    assert df['station'][0] == 'KBOI'

    assert_almost_equal(df['pressure'][0], 919.0, 2)
    assert_almost_equal(df['height'][0], 871.0, 2)
    assert_almost_equal(df['temperature'][0], -0.1, 2)
    assert_almost_equal(df['dewpoint'][0], -0.2, 2)
    assert_almost_equal(df['u_wind'][0], 2.598, 2)
    assert_almost_equal(df['v_wind'][0], 1.500, 2)
    assert_almost_equal(df['speed'][0], 3.0, 1)
    assert_almost_equal(df['direction'][0], 240.0, 1)

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'knot'
    assert df.units['v_wind'] == 'knot'
    assert df.units['speed'] == 'knot'
    assert df.units['direction'] == 'degrees'
    assert df.units['station'] is None
    assert df.units['time'] is None


@recorder.use_cassette('iastate_sounding_with_nans')
def test_interp():
    """Test the interpolation flag for the IA State retrieval."""
    df = IAStateUpperAir.request_data(datetime(2011, 4, 14, 18), 'OUN', interp_nans=True)
    assert not df['temperature'].isnull().any()
    assert not df['dewpoint'].isnull().any()


@recorder.use_cassette('iastate_no_data')
def test_no_data_iastate():
    """Test Iowa State data when no data are available."""
    with pytest.raises(ValueError):
        IAStateUpperAir.request_data(datetime(2010, 12, 9, 1), 'BOI')


@recorder.use_cassette('iastate_no_future_data')
def test_no_future_data_iastate():
    """Test Iowa State data when future data are requested."""
    with pytest.raises(ValueError):
        IAStateUpperAir.request_data(datetime(2999, 12, 9, 12), 'BOI')


@recorder.use_cassette('iastate_all_data_single_pressure')
def test_all_data_single_pressure_iastate():
    """Test Iowa State request for all data at a single pressure level."""
    df = IAStateUpperAir.request_all_data(datetime(1999, 5, 4, 0), pressure=500)
    idx = df.loc[df.station == 'KDDC'].index[0]

    assert df['time'][idx] == datetime(1999, 5, 4, 0)
    assert df['station'][idx] == 'KDDC'

    assert_almost_equal(df['pressure'][idx], 500.0, 2)
    assert_almost_equal(df['height'][idx], 5606.0, 2)
    assert_almost_equal(df['temperature'][idx], -17.2, 2)
    assert_almost_equal(df['dewpoint'][idx], -22.9, 2)
    assert_almost_equal(df['u_wind'][idx], 30.834774, 2)
    assert_almost_equal(df['v_wind'][idx], 35.47135, 2)
    assert_almost_equal(df['speed'][idx], 47.0, 1)
    assert_almost_equal(df['direction'][idx], 221.0, 1)

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'knot'
    assert df.units['v_wind'] == 'knot'
    assert df.units['speed'] == 'knot'
    assert df.units['direction'] == 'degrees'
    assert df.units['station'] is None
    assert df.units['time'] is None


@recorder.use_cassette('iastate_all_data_all_levels')
def test_all_data_all_levels_iastate():
    """Test Iowa State request for all data at all levels."""
    df = IAStateUpperAir.request_all_data(datetime(1999, 5, 4, 0))
    idx = df.loc[df.station == 'KDDC'].index[12]

    assert df['time'][idx] == datetime(1999, 5, 4, 0)
    assert df['station'][idx] == 'KDDC'

    assert_almost_equal(df['pressure'][idx], 700.0, 2)
    assert_almost_equal(df['height'][idx], 2969.0, 2)
    assert_almost_equal(df['temperature'][idx], 5.8, 2)
    assert_almost_equal(df['dewpoint'][idx], -11.7, 2)
    assert_almost_equal(df['u_wind'][idx], 33.234, 2)
    assert_almost_equal(df['v_wind'][idx], 33.234, 2)
    assert_almost_equal(df['speed'][idx], 47.0, 1)
    assert_almost_equal(df['direction'][idx], 225.0, 1)

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'knot'
    assert df.units['v_wind'] == 'knot'
    assert df.units['speed'] == 'knot'
    assert df.units['direction'] == 'degrees'
    assert df.units['station'] is None
    assert df.units['time'] is None


@recorder.use_cassette('iastate_no_future_data_with_pressure')
def test_no_future_data_with_pressure_iastate():
    """Test Iowa State data when future data are requested with the pressure argument."""
    with pytest.raises(ValueError):
        IAStateUpperAir.request_all_data(datetime(2999, 12, 9, 12), pressure=850.)
