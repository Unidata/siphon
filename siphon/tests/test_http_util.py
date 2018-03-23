# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test Siphon's base HTTP helper functionality."""

from datetime import datetime, timedelta

import pytest

from siphon.http_util import (create_http_session, DataQuery, HTTPEndPoint, HTTPError,
                              parse_iso_date, urlopen, utc)
import siphon.testing

recorder = siphon.testing.get_recorder(__file__)


@recorder.use_cassette('top_thredds_catalog')
def test_urlopen():
    """Test siphon's urlopen wrapper."""
    fobj = urlopen('http://thredds-test.unidata.ucar.edu/thredds/catalog.xml')
    assert fobj.read(2) == b'<?'


@recorder.use_cassette('top_thredds_catalog')
def test_session():
    """Test that https sessions contain the proper user agent."""
    session = create_http_session()
    resp = session.get('http://thredds-test.unidata.ucar.edu/thredds/catalog.xml')
    assert resp.request.headers['user-agent'].startswith('Siphon')


def test_parse_iso():
    """Test parsing ISO-formatted dates."""
    parsed = parse_iso_date('2015-06-15T12:00:00Z')
    assert parsed.utcoffset() == timedelta(0)
    assert parsed == datetime(2015, 6, 15, 12, tzinfo=utc)


def test_data_query_basic():
    """Test forming a basic query."""
    dr = DataQuery()
    dr.all_times()
    dr.variables('foo', 'bar')
    query = repr(dr)  # To check repr for once
    assert 'temporal=all' in query
    assert 'var=foo' in query
    assert 'var=bar' in query


def test_data_query_repeated_vars():
    """Test a query properly de-duplicates variables."""
    dr = DataQuery()
    dr.variables('foo', 'bar')
    dr.variables('foo')
    query = str(dr)
    assert query.count('foo') == 1
    assert query.count('bar') == 1


def test_data_query_time_reset():
    """Test query with multiple time-type query fields."""
    dr = DataQuery().all_times().time(datetime.utcnow())
    query = str(dr)
    assert query.startswith('time='), 'Bad string: ' + query
    assert query.count('=') == 1


def test_data_query_time_reset2():
    """Test that time queries replace each other."""
    dr = DataQuery().time(datetime.utcnow()).all_times()
    assert str(dr) == 'temporal=all'


def test_data_query_time_reset3():
    """Test that time queries replace each other with time range."""
    dt = datetime(2015, 6, 12, 12, 0, 0)
    dt2 = datetime(2015, 6, 13, 12, 0, 0)
    dr = DataQuery().all_times().time_range(dt, dt2)
    query = str(dr)
    assert 'time_start=2015-06-12T12' in query, 'Bad string: ' + query
    assert 'time_end=2015-06-13T12' in query, 'Bad string: ' + query
    assert query.count('=') == 2


def test_data_query_time_format():
    """Test that time queries are properly formatted."""
    dt = datetime(2015, 6, 15, 12, 0, 0)
    dr = DataQuery().time(dt)
    query = str(dr)
    assert query == 'time=2015-06-15T12%3A00%3A00'


def test_data_query_spatial_reset():
    """Test that spatial queries reset each other."""
    dr = DataQuery().lonlat_box(1, 2, 3, 4).lonlat_point(-1, -2)
    query = str(dr)
    assert 'latitude=-2' in query
    assert 'longitude=-1' in query
    assert query.count('=') == 2


def test_data_query_spatial_reset2():
    """Test more that spatial queries reset each other."""
    dr = DataQuery().lonlat_point(-1, -2).lonlat_box(1, 2, 3, 4)
    query = str(dr)
    assert 'south=3' in query
    assert 'north=4' in query
    assert 'west=1' in query
    assert 'east=2' in query
    assert query.count('=') == 4


def test_data_query_iter():
    """Test converting a query to a dictionary."""
    dt = datetime.utcnow()
    dr = DataQuery().time(dt).lonlat_point(-1, -2)
    d = dict(dr)

    assert d['time'] == dt.isoformat()
    assert d['latitude'] == -2
    assert d['longitude'] == -1


def test_data_query_items():
    """Test the items method of query."""
    dt = datetime.utcnow()
    dr = DataQuery().time(dt).lonlat_point(-1, -2)
    items = list(dr.items())

    assert ('time', dt.isoformat()) in items
    assert ('latitude', -2) in items
    assert ('longitude', -1) in items


def test_data_query_add():
    """Test adding custom parameters to a query."""
    dr = DataQuery().add_query_parameter(foo='bar')
    assert str(dr) == 'foo=bar'


@recorder.use_cassette('gfs-error-no-header')
def test_http_error_no_header():
    """Test getting an error back without Content-Type."""
    endpoint = HTTPEndPoint('http://thredds.ucar.edu/thredds/ncss/grib/NCEP/GFS/'
                            'Global_0p5deg/GFS_Global_0p5deg_20180223_1200.grib2')
    query = endpoint.query().variables('u-component_of_wind_isobaric')
    query.time(datetime(2018, 2, 23, 22, 28, 49))
    with pytest.raises(HTTPError):
        endpoint.get_query(query)


class TestEndPoint(object):
    """Test the HTTPEndPoint."""

    def setup(self):
        """Set up tests to point to a common server, api, and end point."""
        self.server = 'http://thredds.ucar.edu/'
        self.api = 'thredds/metadata/grib/NCEP/GFS/Global_0p5deg/TwoD'
        self.endpoint = HTTPEndPoint(self.server + self.api)

    def test_basic(self):
        """Test creating a basic query and validating it."""
        q = self.endpoint.query()
        q.all_times()
        assert self.endpoint.validate_query(q), 'Invalid query.'

    @recorder.use_cassette('gfs-metadata-map')
    def test_trailing_slash(self):
        """Test setting up and end point with a url with a trailing slash."""
        endpoint = HTTPEndPoint(self.server + self.api + '/')
        q = endpoint.query()
        q.add_query_parameter(metadata='variableMap')
        resp = endpoint.get_query(q)
        assert resp.content

    @recorder.use_cassette('gfs-metadata-map')
    def test_query(self):
        """Test getting a query."""
        q = self.endpoint.query()
        q.add_query_parameter(metadata='variableMap')
        resp = self.endpoint.get_query(q)
        assert resp.content

    @recorder.use_cassette('gfs-metadata-map-bad')
    def test_get_error(self):
        """Test that getting a bad path raises an error."""
        with pytest.raises(HTTPError):
            self.endpoint.get_path('')

    def test_url_path(self):
        """Test forming a url path from the end point."""
        path = self.endpoint.url_path('foobar.html')
        assert path == self.server + self.api + '/foobar.html'
