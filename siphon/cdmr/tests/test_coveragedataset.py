# Copyright (c) 2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
import warnings

from siphon.testing import get_recorder
from siphon.cdmr.coveragedataset import CoverageDataset

recorder = get_recorder(__file__)

# Ignore warnings about CoverageDataset
warnings.simplefilter('ignore')


@recorder.use_cassette('hrrr_cdmremotefeature')
def test_simple_cdmremotefeature():
    'Just a smoke test for CDMRemoteFeature'
    cd = CoverageDataset('http://localhost:8080/thredds/cdmrfeature/grid/'
                         'test/HRRR_CONUS_2p5km_20160309_1600.grib2')
    assert cd.grids


@recorder.use_cassette('hrrr_cdmremotefeature')
def test_simple_cdmremotefeature_str():
    'Just a smoke test for converting CoverageDataset to str'
    cd = CoverageDataset('http://localhost:8080/thredds/cdmrfeature/grid/'
                         'test/HRRR_CONUS_2p5km_20160309_1600.grib2')
    assert str(cd)
