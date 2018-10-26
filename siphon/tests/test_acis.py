# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test ACIS Web Services API Access."""
from siphon.simplewebservice.acis import acis_request
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@recorder.use_cassette('acis_request')
def test_acis_metadata():
    """Testing ACIS MetaData request."""
    data = acis_request('StnMeta', {'sids': 'KLNK'})

    assert data['meta'][0]['uid'] == 12527


@recorder.use_cassette('acis_stndata')
def test_acis_stndata():
    """Testing ACIS Station Data request."""
    data = acis_request('StnData', {'sid': 'klnk', 'elems': [
                        {'name': 'avgt', 'interval': 'dly'},
                        {'name': 'mint', 'interval': 'dly'}], 'date': '20000101'})

    assert data['meta']['uid'] == 12527
    assert data['data'][0][0] == '2000-01-01'
    assert data['data'][0][1] == '37.5'
    assert data['data'][0][2] == '26'


@recorder.use_cassette('acis_multistndata')
def test_acis_multistn():
    """Testing ACIS Multi Station Data request."""
    data = acis_request('MultiStnData', {'sids': 'klnk,kgso', 'elems': [
                        {'name': 'avgt', 'interval': 'dly'},
                        {'name': 'mint', 'interval': 'dly'}], 'date': '20000101'})

    assert data['data'][0]['meta']['uid'] == 12527
    assert data['data'][0]['data'][0] == '37.5'
    assert data['data'][1]['meta']['uid'] == 13284
    assert data['data'][1]['data'][0] == '49.0'


@recorder.use_cassette('acis_griddata')
def test_acis_griddata():
    """Testing ACIS Gridded Data request."""
    data = acis_request('GridData',
                        {'loc': '-95.36, 29.76', 'sdate': '2000-01', 'edate': '2000-07',
                         'grid': '3', 'elems': [{'name': 'maxt', 'interval': 'mly',
                                                 'reduce': 'max', 'smry': 'max'}]})

    assert data['data'][0][1] == 81


@recorder.use_cassette('acis_general')
def test_acis_general():
    """Testing ACIS General request."""
    data = acis_request('General/state', {'state': 'ne'})

    assert data['meta'][0]['name'] == 'Nebraska'
