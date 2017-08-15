# Copyright (c) 2017 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test dataset access method helpers."""

import os
import tempfile

import pytest

from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
from siphon.testing import get_recorder


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


@recorder.use_cassette('cat_to_open')
def test_dataset_remote_open(nids_url):
    """Test using the remote_open method to request HTTP access."""
    cat = TDSCatalog(nids_url)
    fobj = cat.datasets[0].remote_open()
    assert fobj.read(8) == b'\x01\r\r\n562 '


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
