# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test NCSS access code."""

from contextlib import contextmanager
from datetime import datetime

import numpy as np
import pytest

from siphon.ncss import NCSS, NCSSQuery, ResponseRegistry
import siphon.testing

recorder = siphon.testing.get_recorder(__file__)


def test_ncss_query_proj_box():
    """Test forming a query with a projected bounding box."""
    nq = NCSSQuery().lonlat_point(1, 2).projection_box(-1, -2, -3, -4)
    query = str(nq)
    assert query.count('=') == 4
    assert 'minx=-1' in query
    assert 'maxx=-3' in query
    assert 'miny=-2' in query
    assert 'maxy=-4' in query


def test_ncss_query_vertical_level():
    """Test making a query with a vertical level."""
    nq = NCSSQuery().vertical_level(50000)
    assert str(nq) == 'vertCoord=50000'


def test_ncss_query_add_latlon():
    """Test query when requesting adding lon and lat."""
    nq = NCSSQuery().add_lonlat(True)
    assert str(nq) == 'addLatLon=True'


def test_ncss_query_strides():
    """Test making a query with strides."""
    nq = NCSSQuery().strides(5, 10)
    query = str(nq)
    assert 'timeStride=5' in query
    assert 'horizStride=10' in query


def test_ncss_query_accept():
    """Test making a query with an accept."""
    nq = NCSSQuery().accept('csv')
    assert str(nq) == 'accept=csv'


@contextmanager
def response_context():
    """Override the response handler registry for testing.

    This way we can force unhandled cases.
    """
    old_reg = siphon.ncss.response_handlers
    siphon.ncss.response_handlers = ResponseRegistry()
    yield siphon.ncss.response_handlers
    siphon.ncss.response_handlers = old_reg


# For testing unit handling
def tuple_unit_handler(data, units=None):
    """Return data as a list, with units as necessary."""
    return np.array(data).tolist(), units


@pytest.fixture
@recorder.use_cassette('ncss_test_metadata')
def ncss():
    """Set up tests with default NCSS client."""
    return NCSS('http://thredds.ucar.edu/thredds/ncss/'
                'grib/NCEP/GFS/Global_0p5deg/GFS_Global_0p5deg_20150612_1200.grib2')


@pytest.fixture
def ncss_query(ncss):
    """Set up for tests with a default valid query."""
    dt = datetime(2015, 6, 12, 15, 0, 0)
    q = ncss.query().lonlat_point(-105, 40).time(dt)
    q.variables('Temperature_isobaric', 'Relative_humidity_isobaric')
    return q


def test_good_query(ncss, ncss_query):
    """Test that a good query is properly validated."""
    assert ncss.validate_query(ncss_query)


def test_bad_query(ncss, ncss_query):
    """Test that a query with an unknown variable is invalid."""
    ncss_query.variables('foo')
    assert not ncss.validate_query(ncss_query)


def test_empty_query(ncss):
    """Test that an empty query is invalid."""
    query = ncss.query()
    res = ncss.validate_query(query)
    assert not res
    assert not isinstance(res, set)


def test_bad_query_no_vars(ncss, ncss_query):
    """Test that a query without variables is invalid."""
    ncss_query.var.clear()
    assert not ncss.validate_query(ncss_query)


@recorder.use_cassette('ncss_gfs_xml_point')
def test_xml_point(ncss, ncss_query):
    """Test parsing XML point returns."""
    ncss_query.accept('xml')
    xml_data = ncss.get_data(ncss_query)

    assert 'Temperature_isobaric' in xml_data
    assert 'Relative_humidity_isobaric' in xml_data
    assert xml_data['lat'][0] == 40
    assert xml_data['lon'][0] == -105


@recorder.use_cassette('ncss_gfs_csv_point')
def test_csv_point(ncss, ncss_query):
    """Test parsing CSV point returns."""
    ncss_query.accept('csv')
    csv_data = ncss.get_data(ncss_query)

    assert 'Temperature_isobaric' in csv_data
    assert 'Relative_humidity_isobaric' in csv_data
    assert csv_data['lat'][0] == 40
    assert csv_data['lon'][0] == -105


@recorder.use_cassette('ncss_gfs_csv_point')
def test_unit_handler_csv(ncss, ncss_query):
    """Test unit-handling from CSV returns."""
    ncss_query.accept('csv')
    ncss.unit_handler = tuple_unit_handler
    csv_data = ncss.get_data(ncss_query)

    temp = csv_data['Temperature_isobaric']
    assert len(temp) == 2
    assert temp[1] == 'K'

    relh = csv_data['Relative_humidity_isobaric']
    assert len(relh) == 2
    assert relh[1] == '%'


@recorder.use_cassette('ncss_gfs_xml_point')
def test_unit_handler_xml(ncss, ncss_query):
    """Test unit-handling from XML returns."""
    ncss_query.accept('xml')
    ncss.unit_handler = tuple_unit_handler
    xml_data = ncss.get_data(ncss_query)

    temp = xml_data['Temperature_isobaric']
    assert len(temp) == 2
    assert temp[1] == 'K'

    relh = xml_data['Relative_humidity_isobaric']
    assert len(relh) == 2
    assert relh[1] == '%'


@recorder.use_cassette('ncss_gfs_netcdf_point')
def test_netcdf_point(ncss, ncss_query):
    """Test handling of netCDF point returns."""
    ncss_query.accept('netcdf')
    nc = ncss.get_data(ncss_query)

    assert 'Temperature_isobaric' in nc.variables
    assert 'Relative_humidity_isobaric' in nc.variables
    assert nc.variables['latitude'][0] == 40
    assert nc.variables['longitude'][0] == -105


@recorder.use_cassette('ncss_gfs_netcdf4_point')
def test_netcdf4_point(ncss, ncss_query):
    """Test handling of netCDF4 point returns."""
    ncss_query.accept('netcdf4')
    nc = ncss.get_data(ncss_query)

    assert 'Temperature_isobaric' in nc.variables
    assert 'Relative_humidity_isobaric' in nc.variables
    assert nc.variables['latitude'][0] == 40
    assert nc.variables['longitude'][0] == -105


@recorder.use_cassette('ncss_gfs_vertical_level')
def test_vertical_level(ncss, ncss_query):
    """Test data return from a single vertical level is correct."""
    ncss_query.accept('csv').vertical_level(50000)
    csv_data = ncss.get_data(ncss_query)

    np.testing.assert_almost_equal(csv_data['Temperature_isobaric'], np.array([263.40]), 2)


@recorder.use_cassette('ncss_gfs_csv_point')
def test_raw_csv(ncss, ncss_query):
    """Test CSV point return from a GFS request."""
    ncss_query.accept('csv')
    csv_data = ncss.get_data_raw(ncss_query)

    assert csv_data.startswith(b'date,lat')


@recorder.use_cassette('ncss_gfs_csv_point')
def test_unknown_mime(ncss, ncss_query):
    """Test handling of unknown mimetypes."""
    ncss_query.accept('csv')
    with response_context():
        csv_data = ncss.get_data(ncss_query)
        assert csv_data.startswith(b'date,lat')
