# Copyright (c) 2008-2015 MetPy Developers.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause

from siphon.testing import get_recorder
from siphon.cdmr.cdmremote import CDMRemote

recorder = get_recorder(__file__)


class TestCDMRmote(object):
    'Tests for the CDMRemote HTTP interface'

    def setup(self):
        'Set up all tests to point to the same dataset'
        self.cdmr = CDMRemote('http://localhost:8080/thredds/cdmremote/'
                              'nc4/nc4_pres_temp_4D.nc')

    @recorder.use_cassette('cdmr_cdl')
    def test_cdl(self):
        'Test getting a CDL document from CDMRemote'
        s = self.cdmr.fetch_cdl()
        assert s

    @recorder.use_cassette('cdmr_capabilities')
    def test_capabilities(self):
        'Test getting a capabilities document from CDMRemote'
        s = self.cdmr.fetch_capabilities()
        assert s

    @recorder.use_cassette('cdmr_ncml')
    def test_ncml(self):
        'Test getting an NCML document from CDMRemote'
        s = self.cdmr.fetch_ncml()
        assert s

    @recorder.use_cassette('cdmr_enable_compression')
    def test_enable_compression(self):
        'Test turning on data compression for CDMRemote'
        self.cdmr.deflate = 4
        d = self.cdmr.fetch_data(latitude=[slice(None)])
        assert d
