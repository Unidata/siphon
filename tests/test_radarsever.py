# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test that Radar Server access works properly."""

from datetime import datetime

import pytest
from requests import HTTPError

from siphon.radarserver import BadQueryError, get_radarserver_datasets, RadarQuery, RadarServer
import siphon.testing

recorder = siphon.testing.get_recorder(__file__)


def test_radar_query_one_station():
    """Test that radar query properly works when given a single station."""
    q = RadarQuery()
    q.stations('KTLX')
    assert str(q) == 'stn=KTLX'


def test_radar_query_multiple_stations():
    """Test that radar query properly works when given multiple stations."""
    q = RadarQuery()
    q.stations('KTLX', 'KFTG')
    assert str(q) == 'stn=KTLX&stn=KFTG'


def test_radar_query_chain():
    """Test that radar query method calls can be chained."""
    dt = datetime(2015, 6, 15, 12, 0, 0)
    q = RadarQuery().stations('KFTG').time(dt)
    query = str(q)
    assert 'stn=KFTG' in query
    assert 'time=2015-06-15T12' in query


@pytest.fixture
@recorder.use_cassette('thredds_radarserver_level3_metadata')
def l3client():
    """Set up server and client for level 3 tests."""
    return RadarServer('http://thredds.ucar.edu/thredds/radarServer/nexrad/level3/IDD')


def test_l3_valid_variables(l3client):
    """Test that validating a query respects correct variables."""
    q = l3client.query()
    q.variables('N0Q', 'N0C')
    assert l3client.validate_query(q)


def test_l3_invalid_variables(l3client):
    """Test that validating a query catches incorrect variables."""
    q = l3client.query()
    q.variables('FOO', 'BAR')
    assert not l3client.validate_query(q)


@pytest.fixture
@recorder.use_cassette('thredds_radarserver_metadata')
def l2client():
    """Set up server and client for tests."""
    return RadarServer('http://thredds.ucar.edu/thredds/radarServer/nexrad/level2/IDD')


def test_stations(l2client):
    """Test parsing of the station information from the server."""
    assert 'KFTG' in l2client.stations


def test_float_attrs(l2client):
    """Test parsing of values from the station information on the server."""
    stn = l2client.stations['KFTG']
    assert stn.elevation == 1675.0
    assert stn.latitude == 39.78
    assert stn.longitude == -104.53


def test_metadata(l2client):
    """Test parsing of variable information from server."""
    assert 'Reflectivity' in l2client.variables


def test_valid_stations(l2client):
    """Test validating a query with valid stations."""
    q = l2client.query()
    q.stations('KFTG', 'KTLX')
    assert l2client.validate_query(q), 'Bad validation check'


def test_invalid_stations(l2client):
    """Test validating a query with invalid stations."""
    q = l2client.query()
    q.stations('KFOO', 'KTLX')
    assert not l2client.validate_query(q), 'Bad validation check'


def test_raw_catalog(l2client):
    """Test getting raw catalog bytes."""
    dt = datetime(2015, 6, 15, 12, 0, 0)
    with recorder.use_cassette('thredds_radarserver_level2_single'):
        q = l2client.query().stations('KFTG').time(dt)
        cat = l2client.get_catalog_raw(q).strip()
    assert cat[-10:] == b'</catalog>'


def test_good_query(l2client):
    """Test making a good request."""
    dt = datetime(2015, 6, 15, 12, 0, 0)
    with recorder.use_cassette('thredds_radarserver_level2_single'):
        q = l2client.query().stations('KFTG').time(dt)
        cat = l2client.get_catalog(q)
    assert len(cat.datasets) == 1


@recorder.use_cassette('thredds_radarserver_level3_bad')
def test_bad_query_raises():
    """Test that a bad query raises an error."""
    dt = datetime(2015, 6, 15, 12, 0, 0)
    client = RadarServer('http://thredds.ucar.edu/thredds/radarServer//nexrad/level3/IDD')
    q = client.query().stations('FTG').time(dt)
    with pytest.raises(BadQueryError):
        client.get_catalog(q)


@recorder.use_cassette('thredds_radarserver_level3_good')
def test_good_level3_query():
    """Test that a valid level 3 query succeeds."""
    dt = datetime(2015, 6, 15, 12, 0, 0)
    client = RadarServer('http://thredds.ucar.edu/thredds/radarServer//nexrad/level3/IDD/')
    q = client.query().stations('FTG').time(dt).variables('N0Q')
    cat = client.get_catalog(q)
    assert len(cat.datasets) == 1


@recorder.use_cassette('thredds_radarserver_toplevel')
def test_datasets_no_trailing():
    """Test that passing a url without a trailing slash works."""
    ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds')
    assert len(ds) == 5


@recorder.use_cassette('thredds_radarserver_toplevel')
def test_datasets_trailing():
    """Test that passing a url with a trailing slash works."""
    ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
    assert len(ds) == 5


@recorder.use_cassette('thredds_radarserver_level3_catalog')
def test_datasets_catalog_access():
    """Test that getting datasets returns a proper catalog."""
    ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
    url = ds['NEXRAD Level III Radar from IDD'].follow().catalog_url
    assert RadarServer(url)


@recorder.use_cassette('radarserver_toplevel_denied')
def test_get_rs_datasets_denied_throws():
    """Test that getting radar server datasets raises an error for permission denied."""
    with pytest.raises(HTTPError):
        get_radarserver_datasets('http://thredds-aws.unidata.ucar.edu/thredds/')


@recorder.use_cassette('radarserver_ds_denied')
def test_rs_constructor_throws():
    """Test that setting up radar server access raises an error for permission denied."""
    with pytest.raises(HTTPError):
        RadarServer('http://thredds-aws.unidata.ucar.edu/thredds/'
                    'radarServer/nexrad/level2/S3/')
