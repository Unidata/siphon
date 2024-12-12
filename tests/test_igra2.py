# Copyright (c) 2018,2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test IGRA2 upper air dataset access."""

from datetime import datetime

from numpy.testing import assert_almost_equal
import pytest

from siphon.simplewebservice.igra2 import IGRAUpperAir
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


def subset_date(dt):
    """Create response filter to subset IGRA2 data for a specific date."""
    def subsetter(response):
        """Given a http response, subset the returned zipped data."""
        from io import BytesIO
        from zipfile import ZipFile

        # We're unpacking the zipfile that's returned to reduce the number of lines
        saved_lines = []
        with ZipFile(BytesIO(response['body']['string'])) as zip_product:
            # Open the only file that's in this zip file
            target_filename = zip_product.namelist()[0]
            with zip_product.open(target_filename, 'r') as target_file:
                # Look for the start of useful data based on date string being in the line
                # that starts a data block
                date_str = dt.strftime('%Y %m %d').encode('ascii')
                for line in target_file:
                    if line.startswith(b'#') and date_str in line:
                        break

                # Save all lines from what we found until we get a start block *without*
                # that date string
                saved_lines.append(line)
                for line in target_file:
                    # Putting this first ensures we have at least one extra line in the saved
                    # data so that this code is executed even when running from cassettes
                    saved_lines.append(line)
                    if line.startswith(b'#') and date_str not in line:
                        break

        # Now that we have our lines, make a new zipfile with a single file with the same
        # name that contains only these lines.
        with BytesIO() as modified_bytes:
            with ZipFile(modified_bytes, 'w') as modified_file:
                modified_file.writestr(target_filename, b''.join(saved_lines))
            response['body']['string'] = modified_bytes.getvalue()

        return response

    return subsetter


@recorder.use_cassette('igra2_sounding',
                       before_record_response=subset_date(datetime(2010, 6, 1)))
def test_igra2():
    """Test that we are properly parsing data from the IGRA2 archive."""
    df, _header = IGRAUpperAir.request_data(datetime(2010, 6, 1, 12), 'USM00070026')

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

    assert df.units['pressure'] == 'hPa'
    assert df.units['height'] == 'meter'
    assert df.units['temperature'] == 'degC'
    assert df.units['dewpoint'] == 'degC'
    assert df.units['u_wind'] == 'meter / second'
    assert df.units['v_wind'] == 'meter / second'
    assert df.units['speed'] == 'meter / second'
    assert df.units['direction'] == 'degrees'
    assert df.units['etime'] == 'second'


@recorder.use_cassette('igra2_derived',
                       before_record_response=subset_date(datetime(2014, 9, 10)))
def test_igra2_drvd():
    """Test that we are properly parsing data from the IGRA2 archive."""
    df, _header = IGRAUpperAir.request_data(datetime(2014, 9, 10, 0),
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
    assert_almost_equal(df['relative_humidity_gradient'][5], -75.3, 2)
    assert_almost_equal(df['u_wind'][5], -7.8, 2)
    assert_almost_equal(df['u_wind_gradient'][5], 9.6, 2)
    assert_almost_equal(df['v_wind'][5], -1.2, 2)
    assert_almost_equal(df['v_wind_gradient'][5], 2.7, 2)
    assert_almost_equal(df['refractive_index'][5], 295., 2)

    assert df.units['pressure'] == 'hPa'
    assert df.units['reported_height'] == 'meter'
    assert df.units['calculated_height'] == 'meter'
    assert df.units['temperature'] == 'Kelvin'
    assert df.units['temperature_gradient'] == 'Kelvin / kilometer'
    assert df.units['potential_temperature'] == 'Kelvin'
    assert df.units['potential_temperature_gradient'] == 'Kelvin / kilometer'
    assert df.units['virtual_temperature'] == 'Kelvin'
    assert df.units['virtual_potential_temperature'] == 'Kelvin'
    assert df.units['vapor_pressure'] == 'Pascal'
    assert df.units['saturation_vapor_pressure'] == 'Pascal'
    assert df.units['reported_relative_humidity'] == 'percent'
    assert df.units['calculated_relative_humidity'] == 'percent'
    assert df.units['u_wind'] == 'meter / second'
    assert df.units['u_wind_gradient'] == '(meter / second) / kilometer)'
    assert df.units['v_wind'] == 'meter / second'
    assert df.units['v_wind_gradient'] == '(meter / second) / kilometer)'
    assert df.units['refractive_index'] == 'unitless'


@recorder.use_cassette('igra2_nodata')
def test_igra2_nonexistent():
    """Test behavior when requesting non-existent data."""
    with pytest.raises(ValueError) as err:
        IGRAUpperAir.request_data(datetime.now(), 'NOSUCHSTATION')

    assert 'No data' in str(err.value)


@recorder.use_cassette('igra2_sounding',
                       before_record_response=subset_date(datetime(2010, 6, 1)))
def test_igra2_bad_time_range():
    """Test that we are properly parsing data from the IGRA2 archive."""
    with pytest.raises(ValueError) as err:
        IGRAUpperAir.request_data(datetime(2012, 6, 1, 12), 'USM00070026')

    assert '2010-06-01 00:00:00' in str(err.value)
