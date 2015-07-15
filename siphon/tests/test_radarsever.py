from datetime import datetime

import siphon.testing
from siphon.radarserver import (BadQueryError, RadarQuery, RadarServer,
                                get_radarserver_datasets)

from nose.tools import eq_, raises

recorder = siphon.testing.get_recorder(__file__)


class TestRadarQuery(object):
    def test_one_station(self):
        q = RadarQuery()
        q.stations('KTLX')
        eq_(str(q), 'stn=KTLX')

    def test_multiple_stations(self):
        q = RadarQuery()
        q.stations('KTLX', 'KFTG')
        eq_(str(q), 'stn=KTLX&stn=KFTG')

    def test_chain(self):
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
        eq_(cat[-10:], b'</catalog>')

    @recorder.use_cassette('thredds_radarserver_level2_single')
    def test_good_query(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        q = self.client.query().stations('KFTG').time(dt)
        cat = self.client.get_catalog(q)
        eq_(len(cat.datasets), 1)

    @recorder.use_cassette('thredds_radarserver_level3_bad')
    @raises(BadQueryError)
    def test_bad_query_raises(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        client = RadarServer(self.server + '/nexrad/level3/IDD')
        q = client.query().stations('FTG').time(dt)
        client.get_catalog(q)

    @recorder.use_cassette('thredds_radarserver_level3_good')
    def test_good_level3_query(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        client = RadarServer(self.server + '/nexrad/level3/IDD/')
        q = client.query().stations('FTG').time(dt).variables('N0Q')
        cat = client.get_catalog(q)
        eq_(len(cat.datasets), 1)


class TestRadarServerDatasets(object):
    @recorder.use_cassette('thredds_radarserver_toplevel')
    def test_no_trailing(self):
        ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds')
        eq_(len(ds), 5)

    @recorder.use_cassette('thredds_radarserver_toplevel')
    def test_trailing(self):
        ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
        eq_(len(ds), 5)

    @recorder.use_cassette('thredds_radarserver_level3_catalog')
    def test_catalog_access(self):
        ds = get_radarserver_datasets('http://thredds.ucar.edu/thredds/')
        url = ds['NEXRAD Level III Radar from IDD'].follow().catalog_url
        assert RadarServer(url)
