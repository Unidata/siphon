# Copyright (c) 2014-2016 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test the CDM Remote HTTP API."""
import pytest

from siphon.cdmr.cdmremote import CDMRemote
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@pytest.fixture
def cdmr():
    """Set up all tests to point to the same dataset."""
    return CDMRemote('http://localhost:8080/thredds/cdmremote/nc4/nc4_pres_temp_4D.nc')


@recorder.use_cassette('cdmr_cdl')
def test_cdl(cdmr):
    """Test getting a CDL document from CDMRemote."""
    s = cdmr.fetch_cdl()
    assert s


@recorder.use_cassette('cdmr_capabilities')
def test_capabilities(cdmr):
    """Test getting a capabilities document from CDMRemote."""
    s = cdmr.fetch_capabilities()
    assert s


@recorder.use_cassette('cdmr_ncml')
def test_ncml(cdmr):
    """Test getting an NCML document from CDMRemote."""
    s = cdmr.fetch_ncml()
    assert s


@recorder.use_cassette('cdmr_enable_compression')
def test_enable_compression(cdmr):
    """Test turning on data compression for CDMRemote."""
    cdmr.deflate = 4
    d = cdmr.fetch_data(latitude=[slice(None)])
    assert d
