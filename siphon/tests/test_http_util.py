from datetime import datetime, timedelta

import siphon.testing
from siphon.http_util import (DataQuery, HTTPEndPoint, HTTPError, create_http_session,
                              parse_iso_date, urlopen, utc)

from nose.tools import eq_, raises

recorder = siphon.testing.get_recorder(__file__)


@recorder.use_cassette('top_thredds_catalog')
def test_urlopen():
    fobj = urlopen('http://thredds-test.unidata.ucar.edu/thredds/catalog.xml')
    eq_(fobj.read(2), b'<?')


@recorder.use_cassette('top_thredds_catalog')
def test_session():
    session = create_http_session()
    resp = session.get('http://thredds-test.unidata.ucar.edu/thredds/catalog.xml')
    assert resp.request.headers['user-agent'].startswith('Siphon')


def test_parse_iso():
    parsed = parse_iso_date('2015-06-15T12:00:00Z')
    eq_(parsed.utcoffset(), timedelta(0))
    eq_(parsed, datetime(2015, 6, 15, 12, tzinfo=utc))


class TestDataQuery(object):
    def test_basic(self):
        dr = DataQuery()
        dr.all_times()
        dr.variables('foo', 'bar')
        query = repr(dr)  # To check repr for once
        assert 'temporal=all' in query
        assert 'var=foo' in query
        assert 'var=bar' in query

    def test_repeated_vars(self):
        dr = DataQuery()
        dr.variables('foo', 'bar')
        dr.variables('foo')
        query = str(dr)
        eq_(query.count('foo'), 1)
        eq_(query.count('bar'), 1)

    def test_time_reset(self):
        dr = DataQuery().all_times().time(datetime.utcnow())
        query = str(dr)
        assert query.startswith('time='), 'Bad string: ' + query
        eq_(query.count('='), 1)

    def test_time_reset2(self):
        dr = DataQuery().time(datetime.utcnow()).all_times()
        eq_(str(dr), 'temporal=all')

    def test_time_reset3(self):
        dt = datetime(2015, 6, 12, 12, 0, 0)
        dt2 = datetime(2015, 6, 13, 12, 0, 0)
        dr = DataQuery().all_times().time_range(dt, dt2)
        query = str(dr)
        assert 'time_start=2015-06-12T12' in query, 'Bad string: ' + query
        assert 'time_end=2015-06-13T12' in query, 'Bad string: ' + query
        eq_(query.count('='), 2)

    def test_time_format(self):
        dt = datetime(2015, 6, 15, 12, 0, 0)
        dr = DataQuery().time(dt)
        query = str(dr)
        eq_(query, 'time=2015-06-15T12%3A00%3A00')

    def test_spatial_reset(self):
        dr = DataQuery().lonlat_box(1, 2, 3, 4).lonlat_point(-1, -2)
        query = str(dr)
        assert 'latitude=-2' in query
        assert 'longitude=-1' in query
        eq_(query.count('='), 2)

    def test_spatial_reset2(self):
        dr = DataQuery().lonlat_point(-1, -2).lonlat_box(1, 2, 3, 4)
        query = str(dr)
        assert 'south=3' in query
        assert 'north=4' in query
        assert 'west=1' in query
        assert 'east=2' in query
        eq_(query.count('='), 4)

    def test_iter(self):
        dt = datetime.utcnow()
        dr = DataQuery().time(dt).lonlat_point(-1, -2)
        d = dict(dr)

        eq_(d['time'], dt.isoformat())
        eq_(d['latitude'], -2)
        eq_(d['longitude'], -1)

    def test_items(self):
        dt = datetime.utcnow()
        dr = DataQuery().time(dt).lonlat_point(-1, -2)
        l = list(dr.items())

        assert ('time', dt.isoformat()) in l
        assert ('latitude', -2) in l
        assert ('longitude', -1) in l

    def test_add(self):
        dr = DataQuery().add_query_parameter(foo='bar')
        eq_(str(dr), 'foo=bar')


class TestEndPoint(object):
    def setup(self):
        self.server = 'http://thredds.ucar.edu/'
        self.api = 'thredds/metadata/grib/NCEP/GFS/Global_0p5deg/TwoD'
        self.endpoint = HTTPEndPoint(self.server + self.api)

    def test_basic(self):
        q = self.endpoint.query()
        q.all_times()
        assert self.endpoint.validate_query(q), 'Invalid query.'

    @recorder.use_cassette('gfs-metadata-map')
    def test_trailing_slash(self):
        endpoint = HTTPEndPoint(self.server + self.api + '/')
        q = endpoint.query()
        q.add_query_parameter(metadata='variableMap')
        resp = endpoint.get_query(q)
        assert resp.content

    @recorder.use_cassette('gfs-metadata-map')
    def test_query(self):
        q = self.endpoint.query()
        q.add_query_parameter(metadata='variableMap')
        resp = self.endpoint.get_query(q)
        assert resp.content

    @recorder.use_cassette('gfs-metadata-map-bad')
    @raises(HTTPError)
    def test_get_error(self):
        self.endpoint.get_path('')

    def test_url_path(self):
        path = self.endpoint.url_path('foobar.html')
        eq_(path, self.server + self.api + '/foobar.html')
