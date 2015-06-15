import siphon.testing
from siphon.util import create_http_session, urlopen

from nose.tools import eq_

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
