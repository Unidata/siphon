# Copyright (c) 2013-2017 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test the catalog access API."""

from datetime import datetime
import logging
import warnings

import pytest

from siphon.catalog import get_latest_access_url, TDSCatalog
from siphon.testing import get_recorder

log = logging.getLogger('siphon.catalog')
log.setLevel(logging.WARNING)
log.addHandler(logging.StreamHandler())

recorder = get_recorder(__file__)


@recorder.use_cassette('thredds-test-toplevel-catalog')
def test_basic():
    """Test of parsing a basic catalog."""
    url = 'http://thredds-test.unidata.ucar.edu/thredds/catalog.xml'
    cat = TDSCatalog(url)
    assert 'Forecast Model Data' in cat.catalog_refs


@recorder.use_cassette('thredds-test-latest-gfs-0p5')
def test_access():
    """Test catalog parsing of access methods."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/grib/'
           'NCEP/GFS/Global_0p5deg/latest.xml')
    cat = TDSCatalog(url)
    ds = list(cat.datasets.values())[0]
    assert 'OPENDAP' in ds.access_urls


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_virtual_access():
    """Test access of virtual datasets."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)
    # find the 2D time coordinate "full collection" dataset
    for dataset in list(cat.datasets.values()):
        if 'Full Collection' in dataset.name:
            ds = dataset
            break
    assert 'OPENDAP' in ds.access_urls
    # TwoD is a virtual dataset, so HTTPServer
    # should not be listed here
    assert 'HTTPServer' not in ds.access_urls


@recorder.use_cassette('latest_rap_catalog')
def test_get_latest():
    """Test latest dataset helper function."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
           'grib/NCEP/RAP/CONUS_13km/catalog.xml')
    latest_url = get_latest_access_url(url, 'OPENDAP')
    assert latest_url


@recorder.use_cassette('latest_rap_catalog')
def test_latest_attribute():
    """Test using the catalog latest attribute."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
           'grib/NCEP/RAP/CONUS_13km/catalog.xml')
    cat = TDSCatalog(url)
    assert cat.latest.name == 'RR_CONUS_13km_20150527_0100.grib2'


@recorder.use_cassette('top_level_cat')
def test_tds_top_catalog():
    """Test parsing top-level catalog."""
    url = 'http://thredds.ucar.edu/thredds/catalog.xml'
    cat = TDSCatalog(url)
    assert cat


@recorder.use_cassette('radar_dataset_cat')
def test_simple_radar_cat():
    """Test parsing of radar server catalog."""
    url = 'http://thredds.ucar.edu/thredds/radarServer/nexrad/level2/IDD/dataset.xml'
    cat = TDSCatalog(url)
    assert cat


@recorder.use_cassette('point_feature_dataset_xml')
def test_simple_point_feature_collection_xml():
    """Test accessing point feature top-level catalog."""
    url = ('http://thredds.ucar.edu/thredds/catalog/nws/metar/ncdecoded/catalog.xml'
           '?dataset=nws/metar/ncdecoded/Metar_Station_Data_fc.cdmr')
    cat = TDSCatalog(url)
    assert cat


@recorder.use_cassette('html_then_xml_catalog')
def test_html_link():
    """Test that we fall-back when given an HTML catalog page."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
               'grib/NCEP/RAP/CONUS_13km/catalog.html')
        cat = TDSCatalog(url)
        assert cat


@recorder.use_cassette('follow_cat')
def test_catalog_follow():
    """Test catalog reference following."""
    url = 'http://thredds.ucar.edu/thredds/catalog.xml'
    ref_name = 'Forecast Model Data'
    cat = TDSCatalog(url).catalog_refs[ref_name].follow()
    assert cat


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_order():
    """Test that we properly order datasets parsed from the catalog."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)
    assert list(cat.datasets) == ['Full Collection (Reference / Forecast Time) Dataset',
                                  'Best NAM CONUS 20km Time Series',
                                  'Latest Collection for NAM CONUS 20km']


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_get_by_index():
    """Test that datasets can be accessed by index."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)
    assert cat.datasets[0].name == 'Full Collection (Reference / Forecast Time) Dataset'
    assert cat.datasets[1].name == 'Best NAM CONUS 20km Time Series'
    assert cat.datasets[2].name == 'Latest Collection for NAM CONUS 20km'


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_str():
    """Test that datasets are printed as expected."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)
    assert str(cat.datasets) == ("['Full Collection (Reference / Forecast Time) Dataset', "
                                 "'Best NAM CONUS 20km Time Series', "
                                 "'Latest Collection for NAM CONUS 20km']")


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_nearest_time():
    """Test getting dataset by time using filenames."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)
    nearest = cat.catalog_refs.filter_time_nearest(datetime(2015, 5, 28, 17))
    assert nearest.title == 'NAM_CONUS_20km_noaaport_20150528_1800.grib1'


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_nearest_time_raises():
    """Test getting dataset by time using filenames."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)

    # Datasets doesn't have any timed datasets
    with pytest.raises(ValueError):
        cat.datasets.filter_time_nearest(datetime(2015, 5, 28, 17))


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_time_range():
    """Test getting datasets by time range using filenames."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)
    in_range = cat.catalog_refs.filter_time_range(datetime(2015, 5, 28, 0),
                                                  datetime(2015, 5, 29, 0))
    titles = [item.title for item in in_range]
    assert titles == ['NAM_CONUS_20km_noaaport_20150528_0000.grib1',
                      'NAM_CONUS_20km_noaaport_20150528_0600.grib1',
                      'NAM_CONUS_20km_noaaport_20150528_1200.grib1',
                      'NAM_CONUS_20km_noaaport_20150528_1800.grib1',
                      'NAM_CONUS_20km_noaaport_20150529_0000.grib1']


@recorder.use_cassette('top_level_20km_rap_catalog')
def test_datasets_time_range_raises():
    """Test getting datasets by time range using filenames."""
    url = ('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/NAM/'
           'CONUS_20km/noaaport/catalog.xml')
    cat = TDSCatalog(url)

    # No time-based dataset names
    with pytest.raises(ValueError):
        cat.datasets.filter_time_range(datetime(2015, 5, 28, 0), datetime(2015, 5, 29, 0))


@recorder.use_cassette('top_level_cat')
def test_catalog_ref_order():
    """Test that catalog references are properly ordered."""
    url = 'http://thredds.ucar.edu/thredds/catalog.xml'
    cat = TDSCatalog(url)
    assert list(cat.catalog_refs) == ['Forecast Model Data', 'Forecast Products and Analyses',
                                      'Observation Data', 'Radar Data', 'Satellite Data',
                                      'Unidata case studies']


@recorder.use_cassette('cat_non_standard_context_path')
def test_non_standard_context_path():
    """Test accessing TDS with non-standard Context Path."""
    url = 'http://ereeftds.bom.gov.au/ereefs/tds/catalog/ereef/mwq/P1A/catalog.xml'
    cat = TDSCatalog(url)
    ds = cat.datasets['A20020101.P1A.ANN_MIM_RMP.nc']
    expected = ('http://ereeftds.bom.gov.au/ereefs/tds/dodsC/ereef/mwq/'
                'P1A/A20020101.P1A.ANN_MIM_RMP.nc')
    assert ds.access_urls['OPENDAP'] == expected


@recorder.use_cassette('cat_access_elements')
def test_access_elements():
    """Test parsing access elements in TDS client catalog."""
    url = 'http://oceandata.sci.gsfc.nasa.gov/opendap/SeaWiFS/L3SMI/2001/001/catalog.xml'
    cat = TDSCatalog(url)
    assert len(list(cat.datasets)) != 0


@recorder.use_cassette('cat_only_http')
def test_simple_service_within_compound():
    """Test parsing of a catalog that asks for a single service within a compound one."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/noaaport/text/'
           'tropical/atlantic/hdob/catalog.xml')
    cat = TDSCatalog(url)
    assert (cat.datasets[0].access_urls ==
            {'HTTPServer': 'http://thredds-test.unidata.ucar.edu/thredds/fileServer/noaaport/'
                           'text/tropical/atlantic/hdob/High_density_obs_20170824.txt'})


@recorder.use_cassette('rsmas_ramadda')
def test_ramadda_catalog():
    """Test parsing a catalog from RAMADDA."""
    url = 'http://weather.rsmas.miami.edu/repository?output=thredds.catalog'
    cat = TDSCatalog(url)
    assert len(cat.catalog_refs) == 12
