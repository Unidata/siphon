"""Test IEM Asos Data Downloading."""
from datetime import datetime

from siphon.simplewebservice.iem import IemAsos
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@recorder.use_cassette('iem_request')
def test_iem_download():
    """Test the downloading of IEM ASOS data"""
    start = datetime(2018, 1, 1)
    end = datetime(2018, 1, 1)

    asosCall = IemAsos(['KLNK', 'KGSO', 'KBDU'], start, end)

    stn1 = asosCall.data[(asosCall.data.station == 'GSO')]
    stn2 = asosCall.data[(asosCall.data.station == 'LNK')]
    stn3 = asosCall.data[(asosCall.data.station == 'BDU')]

    assert stn1['station'][1] == 'GSO'
    assert stn2['station'][1] == 'LNK'
    assert stn3['station'][1] == 'BDU'
