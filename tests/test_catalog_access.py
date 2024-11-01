# Copyright (c) 2017 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test dataset access method helpers."""


import logging
import os
import tempfile

import pytest

from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
from siphon.testing import get_recorder

log = logging.getLogger('siphon.catalog')
log.setLevel(logging.WARNING)

recorder = get_recorder(__file__)


@pytest.fixture
def nids_url():
    """Return the URL for accessing the test NIDS dataset."""
    return ('http://thredds.ucar.edu/thredds/catalog/nexrad/level3/NMD/FTG/20170719/catalog.'
            'xml?dataset=NWS/NEXRAD3/NMD/FTG/20170719/Level3_FTG_NMD_20170719_2337.nids')


@recorder.use_cassette('cat_to_subset')
def test_dataset_subset():
    """Test using the subset method to request NCSS access."""
    cat = TDSCatalog('http://thredds.ucar.edu/thredds/catalog/satellite/VIS/'
                     'EAST-CONUS_1km/current/catalog.xml')
    subset = cat.datasets[0].subset()
    assert isinstance(subset, NCSS)
    assert 'VIS' in subset.variables


@recorder.use_cassette('ncei_cat_to_subset')
def test_dataset_subset_ncei():
    """Test using the subset method to request NCSS access from NCEI servers."""
    cat = TDSCatalog('https://www.ncei.noaa.gov/thredds/catalog/narr-a-files/199303/'
                     '19930313/catalog.xml')
    subset = cat.datasets[0].subset()
    assert isinstance(subset, NCSS)
    assert 'Temperature_isobaric' in subset.variables


@recorder.use_cassette('cat_to_open')
def test_dataset_remote_open(nids_url):
    """Test using the remote_open method to request HTTP access."""
    cat = TDSCatalog(nids_url)
    fobj = cat.datasets[0].remote_open()
    assert fobj.read(8) == b'\x01\r\r\n562 '


@recorder.use_cassette('fronts_cat_open')
def test_dataset_remote_open_text():
    """Test using remote_open to get data as text."""
    cat = TDSCatalog('https://thredds-test.unidata.ucar.edu/thredds/catalog/noaaport/text'
                     '/fronts/catalog.xml')
    fobj = cat.datasets[0].remote_open(mode='t', errors='strict')
    assert fobj.read(17) == '\x01\r\r\n109 \r\r\nASUS01'


@recorder.use_cassette('cat_to_cdmr')
def test_dataset_remote_access_default(nids_url):
    """Test using the remote_access method to request access using default method."""
    cat = TDSCatalog(nids_url)
    ds = cat.datasets[0].remote_access()
    assert ds.variables == {}
    assert ds.title == 'Nexrad Level 3 Data'


@recorder.use_cassette('cat_to_cdmr')
def test_dataset_remote_access_cdmr(nids_url):
    """Test using the remote_access method to request CDMR access."""
    cat = TDSCatalog(nids_url)
    ds = cat.datasets[0].remote_access(service='CdmRemote')
    assert ds.variables == {}
    assert ds.title == 'Nexrad Level 3 Data'


@recorder.use_cassette('cat_to_cdmr')
def test_dataset_remote_access_cdmr_xarray(nids_url):
    """Test using the remote_access method to request CDMR using xarray."""
    pytest.importorskip('xarray')
    cat = TDSCatalog(nids_url)
    ds = cat.datasets[0].remote_access(use_xarray=True)
    assert not ds.variables
    assert ds.attrs['title'] == 'Nexrad Level 3 Data'


@recorder.use_cassette('cat_to_open')
def test_dataset_download(nids_url):
    """Test using the download method to download entire dataset."""
    cat = TDSCatalog(nids_url)
    temp = os.path.join(tempfile.gettempdir(), 'siphon-test.temp')
    try:
        assert not os.path.exists(temp)
        cat.datasets[0].download(temp)
        assert os.path.exists(temp)
    finally:
        os.remove(temp)


@recorder.use_cassette('cat_to_open')
def test_dataset_default_download(nids_url):
    """Test using the download method using default filename."""
    cat = TDSCatalog(nids_url)
    temp = os.path.join(tempfile.gettempdir(), cat.datasets[0].name)
    wkdir = os.getcwd()
    try:
        os.chdir(tempfile.gettempdir())
        assert not os.path.exists(temp)
        cat.datasets[0].download()
        assert os.path.exists(temp)
    finally:
        os.remove(temp)
        os.chdir(wkdir)


@recorder.use_cassette('cat_to_open')
def test_dataset_invalid_service_remote_access(nids_url):
    """Test requesting an invalid service for remote_access gives a ValueError."""
    cat = TDSCatalog(nids_url)
    with pytest.raises(ValueError) as err:
        cat.datasets[0].remote_access('foobar')
    assert 'not a valid service for' in str(err.value)


@recorder.use_cassette('cat_to_open')
def test_dataset_invalid_service_subset(nids_url):
    """Test requesting an invalid service for subset gives a ValueError."""
    cat = TDSCatalog(nids_url)
    with pytest.raises(ValueError) as err:
        cat.datasets[0].subset('OPENDAP')
    assert 'not a valid service for' in str(err.value)


@recorder.use_cassette('cat_to_open')
def test_dataset_subset_unavailable(nids_url):
    """Test requesting subset on a dataset that does not have it gives a RuntimeError."""
    cat = TDSCatalog(nids_url)
    with pytest.raises(RuntimeError) as err:
        cat.datasets[0].subset()
    assert 'Subset access is not available' in str(err.value)


@recorder.use_cassette('cat_to_open')
def test_dataset_unavailable_service(nids_url):
    """Test requesting a service that isn't present gives a ValueError."""
    cat = TDSCatalog(nids_url)
    with pytest.raises(ValueError) as err:
        cat.datasets[0].access_with_service('NetcdfSubset')
    assert 'not available' in str(err.value)


@recorder.use_cassette('cat_to_open')
def test_dataset_no_handler(nids_url):
    """Test requesting a service that has no handler gives a ValueError."""
    cat = TDSCatalog(nids_url)
    with pytest.raises(ValueError) as err:
        cat.datasets[0].access_with_service('UDDC')
    assert 'is not an access method supported' in str(err.value)


@recorder.use_cassette('cat_only_http')
def test_case_insensitive_access(caplog):
    """Test case-insensitive parsing of access methods in default catalog."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/noaaport/text/'
           'tropical/atlantic/hdob/catalog.xml')
    cat = TDSCatalog(url)
    access_name = list(cat.datasets[0].access_urls.keys())[0]
    assert access_name == 'HTTPSERVER'  # test __eq__
    assert access_name == 'HTTPSERVER'  # test __eq__
    assert access_name > 'a'  # test __gt__
    assert access_name >= 'a'  # test __ge__
    assert access_name < 'Z'  # test __lt__
    assert access_name <= 'Z'  # test __le__
    assert access_name != 1  # test fail on _try_lower
    assert 'Could not convert 1 to lowercase.' in caplog.text


@recorder.use_cassette('cat_only_http')
def test_manage_access_types_case_insensitive(caplog):
    """Test case-insensitive parsing of access methods in default catalog."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/noaaport/text/'
           'tropical/atlantic/hdob/catalog.xml')
    cat = TDSCatalog(url)
    ds = cat.datasets[0]
    wrong_case_key = 'HTTPSERVER'
    test_string = 'test'
    http_url = ('http://thredds-test.unidata.ucar.edu/thredds/fileServer/noaaport/'
                'text/tropical/atlantic/hdob/High_density_obs_20170824.txt')
    assert ds.access_urls == {'HTTPSERVER': http_url}  # test __eq__
    assert ds.access_urls[wrong_case_key] == http_url  # test __getitem___
    assert wrong_case_key in ds.access_urls  # test __contains__
    ds.access_urls[wrong_case_key] = test_string
    assert ds.access_urls[wrong_case_key] == test_string  # test __setitem__
    assert ds.access_urls.pop(wrong_case_key) == test_string  # test __delitem__
