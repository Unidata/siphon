# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from datetime import datetime

import pytest
from requests import HTTPError

from siphon.radarserver import (BadQueryError, get_radarserver_datasets, RadarQuery,
                                RadarServer)
import siphon.testing

recorder = siphon.testing.get_recorder(__file__)


def test_radar_query_one_station():
    q = RadarQuery()
    q.stations('KTLX')
    assert str(q) == 'stn=KTLX'


def test_radar_query_multiple_stations():
    q = RadarQuery()
    q.stations('KTLX', 'KFTG')
    assert str(q) == 'stn=KTLX&stn=KFTG'


def test_radar_query_chain():
    dt = datetime(2015, 6, 15, 12, 0, 0)
    q = RadarQuery().stations('KFTG').time(dt)
    query = str(q)
    assert 'stn=KFTG' in query
    assert 'time=2015-06-15T12' in query


class TestRadarServerLevel3(object):
    @recorder.use_cassette('thredds_radarserver_level3_metadata')
    def setup(self):
        self.server = 'http://thredds.ucar.edu/thredds/radarServer/'
        self.client = RadarServer(self.server + 'nexrad/level3/IDD')

    def test_valid_variables(self):
        q = self.client.query()
        q.variables('N0Q', 'N0C')
        assert self.client.validate_query(q)

    def test_invalid_variables(self):
        q = self.client.query()
        q.variables('FOO', 'BAR')
        assert not self.client.validate_query(q)


class TestRadarServer(object):
    @recorder.use_cassette('thredds_radarserver_metadata')
    def setup(self):
        self.server = 'http://thredds.ucar.edu/thredds/radarServer/'
        self.client = RadarServer(self.server + 'nexrad/level2/IDD')

    def test_stations(self):
        assert 'KFTG' in self.client.stations

    def test_float_attrs(self):
        stn = self.client.stations['KFTG']
        assert stn.elevation == 1675.0
        assert stn.latitude == 39.78
        assert stn.longitude == -104.53

    def test_metadata(self):
        assert 'Reflectivity' in self.client.variables

    def test_valid_stations(self):
        q = self.client.query()
        q.stations('KFTG', 'KTLX')
        assert self.client.validate_query(q), 'Bad validation check'

    def test_invalid_stations(self):
        q = self.client.query()
        q.stations('KFOO', 'KTLX')
        assert not self.client.validate_query(q), 'Bad validation check'

    @recorder.use_cassette('thredds_radarserver_level2_single')
    def test_raw_catalog(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        q = self.client.query().stations('KFTG').time(dt)
        cat = self.client.get_catalog_raw(q).strip()
        assert cat[-10:] == b'</catalog>'

    @recorder.use_cassette('thredds_radarserver_level2_single')
    def test_good_query(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        q = self.client.query().stations('KFTG').time(dt)
        cat = self.client.get_catalog(q)
        assert len(cat.datasets) == 1

    @recorder.use_cassette('thredds_radarserver_level3_bad')
    def test_bad_query_raises(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        client = RadarServer(self.server + '/nexrad/level3/IDD')
        q = client.query().stations('FTG').time(dt)
        with pytest.raises(BadQueryError):
            client.get_catalog(q)

    @recorder.use_cassette('thredds_radarserver_level3_good')
    def test_good_level3_query(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        client = RadarServer(self.server + '/nexrad/level3/IDD/')
        q = client.query().stations('FTG').time(dt).variables('N0Q')
        cat = client.get_catalog(q)
        assert len(cat.datasets) == 1


class TestRadarServerDatasets(object):
    @recorder.use_cassette('thredds_radarserver_toplevel')
    def test_no_trailing(self):
        ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds')
        assert len(ds) == 5

    @recorder.use_cassette('thredds_radarserver_toplevel')
    def test_trailing(self):
        ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
        assert len(ds) == 5

    @recorder.use_cassette('thredds_radarserver_level3_catalog')
    def test_catalog_access(self):
        ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
        url = ds['NEXRAD Level III Radar from IDD'].follow().catalog_url
        assert RadarServer(url)


@recorder.use_cassette('radarserver_toplevel_denied')
def test_get_rs_datasets_denied_throws():
    with pytest.raises(HTTPError):
        get_radarserver_datasets('http://thredds-aws.unidata.ucar.edu/thredds/')


@recorder.use_cassette('radarserver_ds_denied')
def test_rs_constructor_throws():
    with pytest.raises(HTTPError):
        RadarServer('http://thredds-aws.unidata.ucar.edu/thredds/'
                    'radarServer/nexrad/level2/S3/')
