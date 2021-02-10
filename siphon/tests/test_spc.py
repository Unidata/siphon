# Copyright (c) 2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test Storm Prediction Center access."""

from datetime import datetime

import numpy as np
from numpy.testing import assert_almost_equal
import pytest

from siphon.simplewebservice.spc import SPC
from siphon.simplewebservice.spc import SPCArchive
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


def subset_records(response):
    """Filter to subset SPC archive and only save a subset of records."""
    data = response['body']['string']
    index = 0

    # Grab whole lines up to this maximum size
    while index < 4096:
        index = data.find(b'\n', index + 1)
        if index == -1:
            index = 4096
    response['body']['string'] = data[:index + 1]

    return response


def subset_zipped_records(response):
    """Filter to subset SPC zipped archive and only save a subset of records."""
    from io import BytesIO
    from zipfile import ZipFile

    data = response['body']['string']

    # Unzip and pull out enough bytes to process
    with ZipFile(BytesIO(data)) as zip_product:
        target_filename = zip_product.namelist()[0]
        target_file = zip_product.open(target_filename, 'r')
        data = target_file.read(4200)

    # Grab whole lines up to this maximum size
    index = 0
    while index < 4096:
        index = data.find(b'\n', index + 1)
        if index == -1:
            index = 4096

    # Rezip our truncated file
    with BytesIO() as modified_bytes:
        with ZipFile(modified_bytes, 'w') as modified_file:
            modified_file.writestr(target_filename, data[:index + 1])
        response['body']['string'] = modified_bytes.getvalue()

    return response


@recorder.use_cassette('spc_wind_archive', before_record_response=subset_records)
def test_wind_archive():
    """Test that we are properly parsing wind data from the SPC archive."""
    # Testing wind events for random day in may 20th, 2010
    storms = SPCArchive.get_wind_database(filename='1955-2017_wind.csv')

    assert storms['om'].iloc[0] == 1
    assert storms['Date'].iloc[0] == datetime(1955, 2, 1, 13, 45)
    assert storms['Time Zone'].iloc[0] == 3
    assert storms['State'].iloc[0] == 'AR'
    assert storms['State FIPS'].iloc[0] == 5
    assert storms['State Number'].iloc[0] == 1
    assert storms['Speed'].iloc[0] == 0
    assert storms['Injuries'].iloc[0] == 0
    assert storms['Fatalities'].iloc[0] == 0
    assert storms['Crop Loss'].iloc[0] == 0
    assert storms['Length (mi)'].iloc[0] == 0
    assert storms['Width (yd)'].iloc[0] == 0
    assert storms['ns'].iloc[0] == 0
    assert storms['sn'].iloc[0] == 0
    assert storms['sg'].iloc[0] == 0
    assert storms['County FIPS 1'].iloc[0] == 77
    assert storms['County FIPS 2'].iloc[0] == 0
    assert storms['County FIPS 3'].iloc[0] == 0
    assert storms['County FIPS 4'].iloc[0] == 0
    assert_almost_equal(storms['Property Loss'].iloc[0], 0)
    assert_almost_equal(storms['Start Lat'].iloc[0], 34.78, 3)
    assert_almost_equal(storms['Start Lon'].iloc[0], -90.78, 3)
    assert_almost_equal(storms['End Lat'].iloc[0], 0)
    assert_almost_equal(storms['End Lon'].iloc[0], 0)


@recorder.use_cassette('spc_torn_archive', before_record_response=subset_zipped_records)
def test_torn_archive():
    """Test that we are properly parsing tornado data from the SPC archive."""
    storms = SPCArchive.get_tornado_database()

    assert storms['om'].iloc[0] == 1
    assert storms['Date'].iloc[0] == datetime(1950, 1, 3, 11, 0, 0)
    assert storms['Time Zone'].iloc[0] == 3
    assert storms['State'].iloc[0] == 'MO'
    assert storms['State FIPS'].iloc[0] == 29
    assert storms['State Number'].iloc[0] == 1
    assert storms['F-Scale'].iloc[0] == 3
    assert storms['Injuries'].iloc[0] == 3
    assert storms['Fatalities'].iloc[0] == 0
    assert storms['Property Loss'].iloc[0] == 6
    assert storms['Crop Loss'].iloc[0] == 0
    assert storms['Length (mi)'].iloc[0] == 9.5
    assert storms['Width (yd)'].iloc[0] == 150
    assert storms['ns'].iloc[0] == 2
    assert storms['sn'].iloc[0] == 0
    assert storms['sg'].iloc[0] == 1
    assert storms['County FIPS 1'].iloc[0] == 0
    assert storms['County FIPS 2'].iloc[0] == 0
    assert storms['County FIPS 3'].iloc[0] == 0
    assert storms['County FIPS 4'].iloc[0] == 0
    assert_almost_equal(storms['Start Lat'].iloc[0], 38.77, 3)
    assert_almost_equal(storms['Start Lon'].iloc[0], -90.22, 3)
    assert_almost_equal(storms['End Lat'].iloc[0], 38.83, 3)
    assert_almost_equal(storms['End Lon'].iloc[0], -90.03, 3)


@recorder.use_cassette('spc_hail_archive', before_record_response=subset_records)
def test_hail_archive():
    """Test that we are properly parsing hail data from the SPC archive."""
    storms = SPCArchive.get_hail_database('1955-2017_hail.csv')

    assert storms['om'].iloc[0] == 1
    assert storms['Date'].iloc[0] == datetime(1955, 1, 17, 16, 39)
    assert storms['Time Zone'].iloc[0] == 3
    assert storms['State'].iloc[0] == 'TX'
    assert storms['State FIPS'].iloc[0] == 48
    assert storms['State Number'].iloc[0] == 1
    assert storms['Size'].iloc[0] == 0.75
    assert storms['Injuries'].iloc[0] == 0
    assert storms['Fatalities'].iloc[0] == 0
    assert storms['Property Loss'].iloc[0] == 0
    assert storms['Crop Loss'].iloc[0] == 0
    assert storms['Length (mi)'].iloc[0] == 0
    assert storms['Width (yd)'].iloc[0] == 0
    assert storms['ns'].iloc[0] == 0
    assert storms['sn'].iloc[0] == 0
    assert storms['sg'].iloc[0] == 0
    assert storms['County FIPS 1'].iloc[0] == 227
    assert storms['County FIPS 2'].iloc[0] == 0
    assert storms['County FIPS 3'].iloc[0] == 0
    assert storms['County FIPS 4'].iloc[0] == 0
    assert_almost_equal(storms['Start Lat'].iloc[0], 32.2, 3)
    assert_almost_equal(storms['Start Lon'].iloc[0], -101.5, 3)
    assert_almost_equal(storms['End Lat'].iloc[0], 0.0, 3)
    assert_almost_equal(storms['End Lon'].iloc[0], 0.0, 3)


@recorder.use_cassette('spc_wind_after_2011_archive')
def test_wind_after_2011_archive():
    """Test of method of SPC wind data parsing to be used for recent years."""
    # Second set of assertions for parsing done for storm events after 12/31/2017
    table = SPC.get_wind_reports(datetime(2018, 6, 15))

    assert table['Time'][0] == datetime(2018, 6, 15, 12, 15)
    assert table['Time'][18] == datetime(2018, 6, 16, 0, 28)
    assert table['Speed'][0] == 78
    assert np.isnan(table['Speed'][1])
    assert table['Location'][0] == '13 SSE LITTLE MARAIS'
    assert table['County'][0] == 'LSZ162'
    assert table['State'][0] == 'MN'
    assert_almost_equal(table['Lat'][0], 47.25, 3)
    assert_almost_equal(table['Lon'][0], -90.96, 3)
    assert table['Comments'][0] == 'REPORTED BY THE JAMES R. BARKER. (DLH)'


@recorder.use_cassette('spc_torn_after_2011_archive')
def test_torn_after_2011_archive():
    """Test of method of SPC tornado data parsing to be used for recent years."""
    table = SPC.get_tornado_reports(datetime(2018, 6, 15))

    assert table['Time'][0] == datetime(2018, 6, 15, 22, 25)
    assert np.isnan(table['F_Scale'][0])
    assert table['Location'][0] == '5 W WYNNE'
    assert table['County'][0] == 'CROSS'
    assert table['State'][0] == 'AR'
    assert_almost_equal(table['Lat'].iloc[0], 35.23, 3)
    assert_almost_equal(table['Lon'].iloc[0], -90.88, 3)
    assert table['Comments'][0] == ("A WEAK LANDSPOUT TORNADO OCCURRED NEAR THE L'ANGUILLE "
                                    'RIVER WEST OF WYNNE. NO DAMAGE WAS REPORTED. TIME IS '
                                    'ESTIMATED. (MEG)')


@recorder.use_cassette('spc_hail_after_2011_archive')
def test_hail_after_2011_archive():
    """Test of method of SPC hail data parsing to be used for recent years."""
    table = SPC.get_hail_reports(datetime(2018, 6, 15))

    assert table['Time'][0] == datetime(2018, 6, 15, 13, 35)
    assert_almost_equal(table['Size'][0], 1.0, 2)
    assert table['Location'][0] == 'MOSINEE'
    assert table['County'][0] == 'MARATHON'
    assert table['State'][0] == 'WI'
    assert_almost_equal(table['Lat'][0], 44.78, 3)
    assert_almost_equal(table['Lon'][0], -89.69, 3)
    assert table['Comments'].iloc[0] == '(GRB)'


@recorder.use_cassette('spc_torn_future')
def test_torn_future():
    """Test error retrieval of tornado after current date."""
    with pytest.raises(ValueError):
        SPC.get_tornado_reports(datetime(2050, 5, 20))


@recorder.use_cassette('spc_wind_future')
def test_wind_future():
    """Test error retrieval of wind after current date."""
    with pytest.raises(ValueError):
        SPC.get_wind_reports(datetime(2050, 5, 20))


@recorder.use_cassette('spc_hail_future')
def test_hail_future():
    """Test error retrieval of hail after current date."""
    with pytest.raises(ValueError):
        SPC.get_hail_reports(datetime(2050, 5, 20))


@recorder.use_cassette('spc_torn_before_1950')
def test_torn_before_1950():
    """Test error retrieval of tornado data before 1950."""
    with pytest.raises(ValueError):
        SPC.get_tornado_reports(datetime(1949, 5, 20))


@recorder.use_cassette('spc_wind_before_1955')
def test_wind_before_1955():
    """Test error retrieval of wind data before 1955."""
    with pytest.raises(ValueError):
        SPC.get_wind_reports(datetime(1949, 5, 20))


@recorder.use_cassette('spc_hail_before_1955')
def test_hail_before_1955():
    """Test error retrieval of hail data before 1955."""
    with pytest.raises(ValueError):
        SPC.get_hail_reports(datetime(1949, 5, 20))
