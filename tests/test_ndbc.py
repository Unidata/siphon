# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test National Data Buoy Center (NDBC) dataset access."""

from datetime import datetime

import numpy as np
from numpy.testing import assert_almost_equal, assert_equal
import pytest

from siphon.http_util import utc
from siphon.simplewebservice.ndbc import NDBC
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@recorder.use_cassette('ndbc_realtime_txt')
def test_ndbc_realtime_txt():
    """Test that we are properly parsing realtime txt (met) observations."""
    df = NDBC.realtime_observations('41002')

    assert_almost_equal(df['wind_direction'][3], 150.0, 1)
    assert_almost_equal(df['wind_speed'][3], 7.0, 1)
    assert_almost_equal(df['wind_gust'][3], 8.0, 1)
    assert_almost_equal(df['wave_height'][3], 1.2, 1)
    assert_equal(df['dominant_wave_period'][3], np.nan)
    assert_almost_equal(df['average_wave_period'][3], 4.5, 1)
    assert_almost_equal(df['dominant_wave_direction'][3], 209.0, 1)
    assert_almost_equal(df['pressure'][3], 1022.9, 1)
    assert_equal(df['air_temperature'][3], np.nan)
    assert_almost_equal(df['water_temperature'][3], 28.0, 1)
    assert_equal(df['dewpoint'][3], np.nan)
    assert_equal(df['visibility'][3], np.nan)
    assert_equal(df['3hr_pressure_tendency'][3], np.nan)
    assert_equal(df['water_level_above_mean'][3], np.nan)
    assert df['time'][3] == datetime(2018, 8, 1, 14, 40, tzinfo=utc)

    assert df.units['wind_direction'] == 'degrees'
    assert df.units['wind_speed'] == 'meters/second'
    assert df.units['wind_gust'] == 'meters/second'
    assert df.units['wave_height'] == 'meters'
    assert df.units['dominant_wave_period'] == 'seconds'
    assert df.units['average_wave_period'] == 'seconds'
    assert df.units['dominant_wave_direction'] == 'degrees'
    assert df.units['pressure'] == 'hPa'
    assert df.units['air_temperature'] == 'degC'
    assert df.units['water_temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['visibility'] == 'nautical_mile'
    assert df.units['3hr_pressure_tendency'] == 'hPa'
    assert df.units['water_level_above_mean'] == 'feet'
    assert df.units['time'] is None


@recorder.use_cassette('ndbc_realtime_drift')
def test_ndbc_realtime_drift():
    """Test that we are properly parsing realtime drift observations."""
    df = NDBC.realtime_observations('22101', data_type='drift')

    assert_almost_equal(df['latitude'][3], 37.24, 2)
    assert_almost_equal(df['longitude'][3], 126.02, 2)
    assert_almost_equal(df['wind_direction'][3], 280.0, 1)
    assert_almost_equal(df['wind_speed'][3], 3.0, 1)
    assert_equal(df['wind_gust'][3], np.nan)
    assert_almost_equal(df['pressure'][3], 1003.4, 1)
    assert_equal(df['3hr_pressure_tendency'][3], np.nan)
    assert_almost_equal(df['air_temperature'][3], 25.3, 1)
    assert_almost_equal(df['water_temperature'][3], 22.8, 1)
    assert df['time'][3] == datetime(2018, 8, 1, 8, 0, tzinfo=utc)

    assert df.units['latitude'] == 'degrees'
    assert df.units['longitude'] == 'degrees'
    assert df.units['wind_direction'] == 'degrees'
    assert df.units['wind_speed'] == 'meters/second'
    assert df.units['wind_gust'] == 'meters/second'
    assert df.units['pressure'] == 'hPa'
    assert df.units['air_temperature'] == 'degC'
    assert df.units['water_temperature'] == 'degC'
    assert df.units['3hr_pressure_tendency'] == 'hPa'
    assert df.units['time'] is None


@recorder.use_cassette('ndbc_realtime_cwind')
def test_ndbc_realtime_cwind():
    """Test that we are properly parsing realtime cwind observations."""
    df = NDBC.realtime_observations('41008', data_type='cwind')

    assert_almost_equal(df['wind_direction'][3], 156, 1)
    assert_almost_equal(df['wind_speed'][3], 6.7, 1)
    assert_equal(df['gust_direction'][3], np.nan)
    assert_almost_equal(df['wind_gust'][0], 9.0, 1)
    assert df['gust_time'][0] == datetime(2018, 8, 1, 14, 49, 0, tzinfo=utc)
    assert df['time'][0] == datetime(2018, 8, 1, 14, 50, 0, tzinfo=utc)

    assert df.units['wind_direction'] == 'degrees'
    assert df.units['wind_speed'] == 'meters/second'
    assert df.units['gust_direction'] == 'degrees'
    assert df.units['wind_gust'] == 'meters/second'
    assert df.units['gust_time'] is None
    assert df.units['time'] is None


@recorder.use_cassette('ndbc_realtime_spec')
def test_ndbc_realtime_spec():
    """Test that we are properly parsing realtime spec observations."""
    df = NDBC.realtime_observations('41002', data_type='spec')

    assert_almost_equal(df['significant_wave_height'][3], 1.2, 1)
    assert_almost_equal(df['swell_height'][3], 0.7, 1)
    assert_almost_equal(df['swell_period'][3], 6.7, 1)
    assert_almost_equal(df['wind_wave_height'][3], 1.0, 1)
    assert_almost_equal(df['wind_wave_period'][3], 3.7, 1)
    assert df['swell_direction'][3] == 'SSE'
    assert df['wind_wave_direction'][3] == 'SSE'
    assert df['steepness'][3] == 'STEEP'
    assert_almost_equal(df['average_wave_period'][3], 4.5, 1)
    assert_almost_equal(df['dominant_wave_direction'][3], 150, 1)
    assert df['time'][3] == datetime(2018, 8, 1, 11, 40, 0, tzinfo=utc)

    assert df.units['significant_wave_height'] == 'meters'
    assert df.units['swell_height'] == 'meters'
    assert df.units['swell_period'] == 'seconds'
    assert df.units['wind_wave_height'] == 'meters'
    assert df.units['wind_wave_period'] == 'seconds'
    assert df.units['swell_direction'] is None
    assert df.units['wind_wave_direction'] is None
    assert df.units['steepness'] is None
    assert df.units['average_wave_period'] == 'seconds'
    assert df.units['dominant_wave_direction'] == 'degrees'
    assert df.units['time'] is None


@recorder.use_cassette('ndbc_realtime_ocean')
def test_ndbc_realtime_ocean():
    """Test that we are properly parsing realtime ocean observations."""
    df = NDBC.realtime_observations('45183', data_type='ocean')

    assert_almost_equal(df['measurement_depth'][3], 1.0, 1)
    assert_equal(df['ocean_temperature'][3], np.nan)
    assert_equal(df['conductivity'][3], np.nan)
    assert_equal(df['salinity'][3], np.nan)
    assert_almost_equal(df['oxygen_concentration'][3], 106.4, 1)
    assert_almost_equal(df['oxygen_concentration_ppm'][3], 9.52, 1)
    assert_equal(df['chlorophyll_concentration'][3], np.nan)
    assert_almost_equal(df['turbidity'][3], 0, 1)
    assert_almost_equal(df['pH'][3], 8.38, 1)
    assert_equal(df['Eh'][3], np.nan)
    assert df['time'][3] == datetime(2018, 8, 1, 13, 30, 0, tzinfo=utc)

    assert (df.units['measurement_depth'] == 'meters')
    assert (df.units['ocean_temperature'] == 'degC')
    assert (df.units['conductivity'] == 'milliSiemens/centimeter')
    assert (df.units['salinity'] == 'psu')
    assert (df.units['oxygen_concentration'] == 'percent')
    assert (df.units['oxygen_concentration_ppm'] == 'ppm')
    assert (df.units['chlorophyll_concentration'] == 'micrograms/liter')
    assert (df.units['turbidity'] == 'ftu')
    assert (df.units['pH'] == 'dimensionless')
    assert (df.units['Eh'] == 'millivolts')
    assert (df.units['time'] is None)


@recorder.use_cassette('ndbc_realtime_srad')
def test_ndbc_realtime_srad():
    """Test that we are properly parsing realtime srad observations."""
    df = NDBC.realtime_observations('45027', data_type='srad')

    assert_almost_equal(df['shortwave_radiation_licor'][3], 51.6, 1)
    assert_equal(df['shortwave_radiation_eppley'][3], np.nan)
    assert_equal(df['longwave_radiation'][3], np.nan)
    assert df['time'][3] == datetime(2018, 8, 1, 14, 30, tzinfo=utc)

    assert (df.units['shortwave_radiation_licor'] == 'watts/meter^2')
    assert (df.units['shortwave_radiation_eppley'] == 'watts/meter^2')
    assert (df.units['longwave_radiation'] == 'watts/meter^2')
    assert (df.units['time'] is None)


@recorder.use_cassette('ndbc_realtime_dart')
def test_ndbc_realtime_dart():
    """Test that we are properly parsing realtime dart observations."""
    df = NDBC.realtime_observations('41421', data_type='dart')

    assert_almost_equal(df['measurement_type'][3], 15, 1)
    assert_almost_equal(df['height'][3], 5806.845, 3)
    assert df['time'][3] == datetime(2018, 8, 1, 11, 15, tzinfo=utc)

    assert (df.units['measurement_type'] == 'minutes')
    assert (df.units['height'] == 'meters')
    assert (df.units['time'] is None)


@recorder.use_cassette('ndbc_realtime_supl')
def test_ndbc_realtime_supl():
    """Test that we are properly parsing realtime supl observations."""
    df = NDBC.realtime_observations('PVGF1', data_type='supl')

    assert_almost_equal(df['hourly_low_pressure'][3], 1019.0, 1)
    assert df['hourly_low_pressure_time'][3] == datetime(2018, 7, 31, 14, 36,
                                                         tzinfo=utc)
    assert_almost_equal(df['hourly_high_wind'][3], 6, 1)
    assert_equal(df['hourly_high_wind_direction'][3], np.nan)
    assert df['hourly_high_wind_time'][3] == datetime(2018, 7, 31, 14, 36,
                                                      tzinfo=utc)
    assert df['time'][3] == datetime(2018, 7, 31, 14, 42, tzinfo=utc)

    assert (df.units['hourly_low_pressure'] == 'hPa')
    assert (df.units['hourly_low_pressure_time'] is None)
    assert (df.units['hourly_high_wind'] == 'meters/second')
    assert (df.units['hourly_high_wind_direction'] == 'degrees')
    assert (df.units['hourly_high_wind_time'] is None)
    assert (df.units['time'] is None)


@recorder.use_cassette('ndbc_realtime_rain')
def test_ndbc_realtime_rain():
    """Test that we are properly parsing realtime rain observations."""
    df = NDBC.realtime_observations('BDVF1', data_type='rain')

    assert_almost_equal(df['hourly_accumulation'][3], 0.0, 1)
    assert df['time'][3] == datetime(2018, 8, 1, 11, tzinfo=utc)

    assert (df.units['hourly_accumulation'] == 'millimeters')
    assert (df.units['time'] is None)


@recorder.use_cassette('ndbc_latest')
def test_ndbc_latest():
    """Test that we are properly parsing latest NDBC observations."""
    df = NDBC.latest_observations()

    assert df['station'][10] == '41004'
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
    assert df['time'][10] == datetime(2018, 7, 30, 21, 10, tzinfo=utc)

    assert df.units['station'] is None
    assert df.units['latitude'] == 'degrees'
    assert df.units['longitude'] == 'degrees'
    assert df.units['wind_direction'] == 'degrees'
    assert df.units['wind_speed'] == 'meters/second'
    assert df.units['wind_gust'] == 'meters/second'
    assert df.units['wave_height'] == 'meters'
    assert df.units['dominant_wave_period'] == 'seconds'
    assert df.units['average_wave_period'] == 'seconds'
    assert df.units['dominant_wave_direction'] == 'degrees'
    assert df.units['pressure'] == 'hPa'
    assert df.units['air_temperature'] == 'degC'
    assert df.units['water_temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['visibility'] == 'nautical_mile'
    assert df.units['3hr_pressure_tendency'] == 'hPa'
    assert df.units['water_level_above_mean'] == 'feet'
    assert df.units['time'] is None


@recorder.use_cassette('ndbc_buoy_data_types')
def test_ndbc_buoy_data_types():
    """Test determination of available buoy data."""
    resp = NDBC.buoy_data_types('41002')
    truth = {'txt': 'standard meteorological data',
             'spec': 'spectral wave summaries',
             'data_spec': 'raw spectral wave data',
             'swdir': 'spectral wave data (alpha1)',
             'swdir2': 'spectral wave data (alpha2)',
             'swr1': 'spectral wave data (r1)',
             'swr2': 'spectral wave data (r2)',
             'supl': 'supplemental measurements data'}
    assert resp == truth


def test_ndbc_realtime_keyerror():
    """Ensure an error is raised for invalid parsed data type requests."""
    with pytest.raises(KeyError):
        NDBC.realtime_observations('41002', data_type='dartt')
