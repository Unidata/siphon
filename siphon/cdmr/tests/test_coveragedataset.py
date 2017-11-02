# Copyright (c) 2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Test Coverage Dataset."""

import pytest

from siphon.cdmr.coveragedataset import CoverageDataset
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


@pytest.mark.filterwarnings('ignore: CoverageDataset')
@recorder.use_cassette('hrrr_cdmremotefeature')
def test_simple_cdmremotefeature():
    """Smoke test for CDMRemoteFeature."""
    cd = CoverageDataset('http://localhost:8080/thredds/cdmrfeature/grid/'
                         'test/HRRR_CONUS_2p5km_20160309_1600.grib2')
    assert cd.grids


@pytest.mark.filterwarnings('ignore: CoverageDataset')
@recorder.use_cassette('hrrr_cdmremotefeature')
def test_simple_cdmremotefeature_str():
    """Smoke test for converting CoverageDataset to str."""
    cd = CoverageDataset('http://localhost:8080/thredds/cdmrfeature/grid/'
                         'test/HRRR_CONUS_2p5km_20160309_1600.grib2')
    assert str(cd)
