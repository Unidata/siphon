from io import BytesIO
from siphon.testing import get_recorder
from siphon.cdmr.ncstream import read_ncstream_messages, read_var_int
from siphon.cdmr.ncStream_pb2 import Header

from nose.tools import eq_

HEAD_LOCATION_DEFAULT = ''
HEAD_TITLE_DEFAULT = ''
HEAD_ID_DEFAULT = ''
HEAD_VERSION_DEFAULT = 0

recorder = get_recorder(__file__)


@recorder.use_cassette('latest_rap_catalog')
def get_test_latest_url(query=None):
    from siphon.catalog import TDSCatalog
    cat = TDSCatalog('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
                     'grib/NCEP/RAP/CONUS_13km/latest.xml')
    url = list(cat.datasets.values())[0].access_urls['CdmRemote']
    if query:
        url += '?' + query
    return url


@recorder.use_cassette('latest_rap_ncstream_header')
def get_header_remote():
    from siphon.http_util import urlopen
    return urlopen(get_test_latest_url('req=header'))


def test_var_int():
    for src, truth in [(b'\xb6\xe0\x02', 45110), (b'\x17\n\x0b', 23)]:
        yield check_var_int, src, truth


def check_var_int(src, result):
    eq_(read_var_int(BytesIO(src)), result)


def test_header_message_def():
    f = get_header_remote()
    messages = read_ncstream_messages(f)
    eq_(len(messages), 1)
    assert isinstance(messages[0], Header)
    head = messages[0]
    # test that the header message definition has not changed!
    test = head.location == HEAD_LOCATION_DEFAULT
    assert [test, not test][head.HasField("location")]
    test = head.title == HEAD_TITLE_DEFAULT
    assert [test, not test][head.HasField("title")]
    test = head.title == HEAD_ID_DEFAULT
    assert [test, not test][head.HasField("id")]
    test = head.title == HEAD_VERSION_DEFAULT
    assert [test, not test][head.HasField("version")]


def test_remote_header():
    f = get_header_remote()
    messages = read_ncstream_messages(f)
    eq_(len(messages), 1)
    assert isinstance(messages[0], Header)

    head = messages[0]
    # make sure fields in the message are set to non-default values
    #  when HasField returns True
    for field in head.ListFields():
        fname = field[0].name
        if not fname == "root":
            test = eval("head.{} == HEAD_{}_DEFAULT".format(fname, fname.upper()))
            assert eval("[{}, not {}][head.HasField('{}')]".format(test, test, fname))


def test_local_data():
    f = BytesIO(b'\xab\xec\xce\xba\x17\n\x0breftime_ISO\x10\x07\x1a\x04\n'
                b'\x02\x10\x01(\x02\x01\x142014-10-28T21:00:00Z')
    messages = read_ncstream_messages(f)
    eq_(len(messages), 1)
    eq_(messages[0][0], b'2014-10-28T21:00:00Z')
