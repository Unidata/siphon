# Copyright (c) 2014-2016 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test the low-level ncstream interface."""

from io import BytesIO

import pytest

from siphon.cdmr.ncstream import read_ncstream_messages, read_var_int
from siphon.cdmr.ncStream_pb2 import Header
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@recorder.use_cassette('latest_rap_catalog')
def get_test_latest_url(query=None):
    """Get the latest URL for testing."""
    from siphon.catalog import TDSCatalog
    cat = TDSCatalog('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
                     'grib/NCEP/RAP/CONUS_13km/latest.xml')
    url = list(cat.datasets.values())[0].access_urls['CdmRemote']
    if query:
        url += '?' + query
    return url


@recorder.use_cassette('latest_rap_ncstream_header')
def get_header_remote():
    """Get a header from a remote data source."""
    from siphon.http_util import session_manager
    return session_manager.urlopen(get_test_latest_url('req=header'))


@pytest.mark.parametrize('src, result', [(b'\xb6\xe0\x02', 45110), (b'\x17\n\x0b', 23)])
def test_read_var_int(src, result):
    """Check that we properly read variable length integers."""
    assert read_var_int(BytesIO(src)) == result


def test_header_message_def():
    """Test parsing of Header message."""
    f = get_header_remote()
    messages = read_ncstream_messages(f)
    assert len(messages) == 1
    assert isinstance(messages[0], Header)
    head = messages[0]
    assert head.location == ('http://thredds-test.unidata.ucar.edu/thredds/cdmremote/grib/'
                             'NCEP/RAP/CONUS_13km/RR_CONUS_13km_20150519_0300.grib2')
    assert head.title == ''
    assert head.id == ''
    assert head.version == 1


def test_local_data():
    """Test reading ncstream messages directly from bytes in a file-like object."""
    f = BytesIO(b'\xab\xec\xce\xba\x17\n\x0breftime_ISO\x10\x07\x1a\x04\n'
                b'\x02\x10\x01(\x02\x01\x142014-10-28T21:00:00Z')
    messages = read_ncstream_messages(f)
    assert len(messages) == 1
    assert messages[0][0] == '2014-10-28T21:00:00Z'


def test_bad_magic(caplog):
    """Test that we get notified of bad magic bytes in stream."""
    # Try reading a bad message
    f = BytesIO(b'\x00\x01\x02\x03')
    read_ncstream_messages(f)

    assert 'Unknown magic' in caplog.text
