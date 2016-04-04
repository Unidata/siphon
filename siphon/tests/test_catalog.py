# Copyright (c) 2013-2015 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

import logging
import warnings

from siphon.testing import get_recorder
from siphon.catalog import TDSCatalog, get_latest_access_url

log = logging.getLogger("siphon.catalog")
log.setLevel(logging.WARNING)
log.addHandler(logging.StreamHandler())

recorder = get_recorder(__file__)


class TestCatalog(object):
    baseURL = 'http://thredds-test.unidata.ucar.edu/thredds/'

    @recorder.use_cassette('thredds-test-toplevel-catalog')
    def test_basic(self):
        url = self.baseURL + 'catalog.xml'
        cat = TDSCatalog(url)
        assert 'Forecast Model Data' in cat.catalog_refs

    @recorder.use_cassette('thredds-test-latest-gfs-0p5')
    def test_access(self):
        url = self.baseURL + 'catalog/grib/NCEP/GFS/Global_0p5deg/latest.xml'
        cat = TDSCatalog(url)
        ds = list(cat.datasets.values())[0]
        assert 'OPENDAP' in ds.access_urls

    @recorder.use_cassette('top_level_20km_rap_catalog')
    def test_virtual_access(self):
        url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
               'CONUS_20km/noaaport/catalog.xml')
        cat = TDSCatalog(url)
        # find the 2D time coordinate "full collection" dataset
        for dataset in list(cat.datasets.values()):
            if "Full Collection" in dataset.name:
                ds = dataset
                break
        assert 'OPENDAP' in ds.access_urls
        # TwoD is a virtual dataset, so HTTPServer
        # should not be listed here
        assert 'HTTPServer' not in ds.access_urls

    @recorder.use_cassette('latest_rap_catalog')
    def test_get_latest(self):
        url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
               'grib/NCEP/RAP/CONUS_13km/catalog.xml')
        latest_url = get_latest_access_url(url, "OPENDAP")
        assert latest_url

    @recorder.use_cassette('top_level_cat')
    def test_tds_top_catalog(self):
        url = 'http://thredds.ucar.edu/thredds/catalog.xml'
        cat = TDSCatalog(url)
        assert cat

    @recorder.use_cassette('radar_dataset_cat')
    def test_simple_radar_cat(self):
        url = 'http://thredds.ucar.edu/thredds/radarServer/nexrad/level2/' \
              'IDD/dataset.xml'
        cat = TDSCatalog(url)
        assert cat

    @recorder.use_cassette('point_feature_dataset_xml')
    def test_simple_point_feature_collection_xml(self):
        url = 'http://thredds.ucar.edu/thredds/catalog/nws/metar/' \
              'ncdecoded/catalog.xml?dataset=nws/metar/ncdecoded' \
              '/Metar_Station_Data_fc.cdmr'
        cat = TDSCatalog(url)
        assert cat

    @recorder.use_cassette('html_then_xml_catalog')
    def test_html_link(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
                   'grib/NCEP/RAP/CONUS_13km/catalog.html')
            cat = TDSCatalog(url)
            assert cat

    @recorder.use_cassette('follow_cat')
    def test_catalog_follow(self):
        url = 'http://thredds.ucar.edu/thredds/catalog.xml'
        ref_name = 'Forecast Model Data'
        cat = TDSCatalog(url).catalog_refs[ref_name].follow()
        assert cat

    @recorder.use_cassette('top_level_20km_rap_catalog')
    def test_datasets_order(self):
        url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
               'CONUS_20km/noaaport/catalog.xml')
        cat = TDSCatalog(url)
        assert list(cat.datasets) == ['Full Collection (Reference / Forecast Time) Dataset',
                                      'Best NAM CONUS 20km Time Series',
                                      'Latest Collection for NAM CONUS 20km']

    @recorder.use_cassette('top_level_cat')
    def test_catalog_ref_order(self):
        url = 'http://thredds.ucar.edu/thredds/catalog.xml'
        cat = TDSCatalog(url)
        assert list(cat.catalog_refs) == ['Forecast Model Data',
                                          'Forecast Products and Analyses', 'Observation Data',
                                          'Radar Data', 'Satellite Data',
                                          'Unidata case studies']
