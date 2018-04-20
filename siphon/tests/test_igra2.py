# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test IGRA2 upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal

from siphon.simplewebservice.igra2 import IGRAUpperAir
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


@recorder.use_cassette('igra2_sounding')
def test_igra2():
    """Test that we are properly parsing data from the IGRA2 archive."""
    df, header = IGRAUpperAir.request_data(datetime(2010, 6, 1, 12), 'USM00070026')

    assert_almost_equal(df['lvltyp1'][5], 1, 1)
    assert_almost_equal(df['lvltyp2'][5], 0, 1)
    assert_almost_equal(df['etime'][5], 126, 2)
    assert_almost_equal(df['pressure'][5], 925.0, 2)
    assert_almost_equal(df['pflag'][5], 0, 1)
    assert_almost_equal(df['height'][5], 696., 2)
    assert_almost_equal(df['zflag'][5], 2, 1)
    assert_almost_equal(df['temperature'][5], -3.2, 2)
    assert_almost_equal(df['tflag'][5], 2, 1)
    assert_almost_equal(df['relative_humidity'][5], 96.3, 2)
    assert_almost_equal(df['direction'][5], 33.0, 2)
    assert_almost_equal(df['speed'][5], 8.2, 2)
    assert_almost_equal(df['u_wind'][5], -4.5, 2)
    assert_almost_equal(df['v_wind'][5], -6.9, 2)
    assert_almost_equal(df['dewpoint'][5], -3.7, 2)

    assert(df.units['pressure'] == 'hPa')
    assert(df.units['height'] == 'meter')
    assert(df.units['temperature'] == 'degC')
    assert(df.units['dewpoint'] == 'degC')
    assert(df.units['u_wind'] == 'meter / second')
    assert(df.units['v_wind'] == 'meter / second')
    assert(df.units['speed'] == 'meter / second')
    assert(df.units['direction'] == 'degrees')
    assert(df.units['etime'] == 'second')


@recorder.use_cassette('igra2_derived')
def test_igra2_drvd():
    """Test that we are properly parsing data from the IGRA2 archive."""
    df, header = IGRAUpperAir.request_data(datetime(2014, 9, 10, 0),
                                           'USM00070026', derived=True)

    assert_almost_equal(df['pressure'][5], 947.43, 2)
    assert_almost_equal(df['reported_height'][5], 610., 2)
    assert_almost_equal(df['calculated_height'][5], 610., 2)
    assert_almost_equal(df['temperature'][5], 269.1, 2)
    assert_almost_equal(df['temperature_gradient'][5], 0.0, 2)
    assert_almost_equal(df['potential_temperature'][5], 273.2, 2)
    assert_almost_equal(df['potential_temperature_gradient'][5], 11.0, 2)
    assert_almost_equal(df['virtual_temperature'][5], 269.5, 2)
    assert_almost_equal(df['virtual_potential_temperature'][5], 273.7, 2)
    assert_almost_equal(df['vapor_pressure'][5], 4.268, 2)
    assert_almost_equal(df['saturation_vapor_pressure'][5], 4.533, 2)
    assert_almost_equal(df['reported_relative_humidity'][5], 93.9, 2)
    assert_almost_equal(df['calculated_relative_humidity'][5], 94.1, 2)
    assert_almost_equal(df['u_wind'][5], -75.3, 2)
    assert_almost_equal(df['u_wind_gradient'][5], -7.8, 2)
    assert_almost_equal(df['v_wind'][5], 9.6, 2)
    assert_almost_equal(df['v_wind_gradient'][5], -1.2, 2)
    assert_almost_equal(df['refractive_index'][5], 27.0, 2)

    assert(df.units['pressure'] == 'hPa')
    assert(df.units['reported_height'] == 'meter')
    assert(df.units['calculated_height'] == 'meter')
    assert(df.units['temperature'] == 'Kelvin')
    assert(df.units['temperature_gradient'] == 'Kelvin / kilometer')
    assert(df.units['potential_temperature'] == 'Kelvin')
    assert(df.units['potential_temperature_gradient'] == 'Kelvin / kilometer')
    assert(df.units['virtual_temperature'] == 'Kelvin')
    assert(df.units['virtual_potential_temperature'] == 'Kelvin')
    assert(df.units['vapor_pressure'] == 'Pascal')
    assert(df.units['saturation_vapor_pressure'] == 'Pascal')
    assert(df.units['reported_relative_humidity'] == 'percent')
    assert(df.units['calculated_relative_humidity'] == 'percent')
    assert(df.units['u_wind'] == 'meter / second')
    assert(df.units['u_wind_gradient'] == '(meter / second) / kilometer)')
    assert(df.units['v_wind'] == 'meter / second')
    assert(df.units['v_wind_gradient'] == '(meter / second) / kilometer)')
    assert(df.units['refractive_index'] == 'unitless')
