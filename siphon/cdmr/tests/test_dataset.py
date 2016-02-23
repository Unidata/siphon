# Copyright (c) 2013-2015 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from siphon.testing import get_recorder
from siphon.cdmr import Dataset
from numpy.testing import assert_almost_equal

recorder = get_recorder(__file__)


def get_fixed_url():
    return ('http://thredds-dev.unidata.ucar.edu/thredds/cdmremote/'
            'grib/NCEP/RAP/CONUS_13km/RR_CONUS_13km_20150518_1200.grib2/GC')


class TestDataset(object):
    @classmethod
    @recorder.use_cassette('rap_ncstream_header')
    def setup_class(cls):
        cls.ds = Dataset(get_fixed_url())

    def test_dataset(self):
        assert hasattr(self.ds, 'Conventions')
        assert 'featureType' in self.ds.ncattrs()

    def test_variable(self):
        assert 'Temperature_isobaric' in self.ds.variables
        assert 'Convective_available_potential_energy_surface' in self.ds.variables

    @recorder.use_cassette('rap_ncstream_var')
    def test_variable_attrs(self):
        var = self.ds.variables['Temperature_isobaric']
        assert hasattr(var, 'units')
        assert 'long_name' in var.ncattrs()


@recorder.use_cassette('rap_compressed')
def test_compression():
    ds = Dataset(get_fixed_url())
    var = ds.variables['Temperature_isobaric']
    subset = var[0, 0]
    assert subset.shape == var.shape[2:]
    assert_almost_equal(subset[0, 0], 206.65640259, 6)


@recorder.use_cassette('nc4_enum')
def test_enum():
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/test_enum_type.nc')
    var = ds.variables['primary_cloud'][:]
    assert var[0] == 0
    assert var[1] == 2
    assert var[2] == 0
    assert var[3] == 1
    assert var[4] == 255


@recorder.use_cassette('nc4_opaque')
def test_opaque():
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_opaques.nc')
    var = ds.variables['var'][:]
    assert var.shape == (3,)
    assert var[0] == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                      b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


@recorder.use_cassette('nc4_groups')
def test_groups():
    "Test that a variable's path includes any parent groups"
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_groups.nc')
    var = ds.groups['g1'].variables['var']

    # Need to check actual path because sample file's header includes data--no request
    # necessary
    assert var.path == '/g1/var'

    dat = var[:]
    assert dat.shape == (1,)


@recorder.use_cassette('nc4_groups')
def test_print():
    "Test that __str__ (or printing) a dataset works"
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_groups.nc')
    s = str(ds)
    truth = """Groups:
g1
Dimensions:
<class 'siphon.cdmr.dataset.Dimension'> name = dim, size = 1
Variables:
<class 'siphon.cdmr.dataset.Variable'>
float32 var(dim)
\tunits: km/hour
\t_ChunkSizes: 1
shape = 1
Attributes:
\ttitle: in first group
---end group---
g2
Groups:
g3
Dimensions:
<class 'siphon.cdmr.dataset.Dimension'> name = dim, size = 3
Variables:
<class 'siphon.cdmr.dataset.Variable'>
float32 var(dim)
\tunits: mm/msec
\t_ChunkSizes: 3
shape = 3
Attributes:
\ttitle: in third group
---end group---
Dimensions:
<class 'siphon.cdmr.dataset.Dimension'> name = dim, size = 2
Variables:
<class 'siphon.cdmr.dataset.Variable'>
float32 var(dim)
\tunits: cm/sec
\t_ChunkSizes: 2
shape = 2
Attributes:
\ttitle: in second group
---end group---
Dimensions:
<class 'siphon.cdmr.dataset.Dimension'> name = dim, size = 4
Variables:
<class 'siphon.cdmr.dataset.Variable'>
float32 var(dim)
\tunits: m/s
\t_ChunkSizes: 4
shape = 4
Attributes:
\ttitle: for testing groups"""
    assert s == truth


class TestIndexing(object):
    @classmethod
    @recorder.use_cassette('rap_ncstream_header')
    def setup_class(cls):
        url = get_fixed_url()
        ds = Dataset(url)
        cls.var = ds.variables['Temperature_isobaric']

    @recorder.use_cassette('rap_ncstream_slices')
    def test_slices(self):
        subset = self.var[1:2, 1:3, 4:7, 8:12]
        assert subset.shape, (1, 2, 3 == 4)

    @recorder.use_cassette('rap_ncstream_first_index')
    def test_first_index(self):
        subset = self.var[5, 10]
        assert subset.shape == self.var.shape[2:]

    @recorder.use_cassette('rap_ncstream_ellipsis_middle')
    def test_ellipsis_middle(self):
        subset = self.var[2, ..., 3]
        assert subset.shape == self.var.shape[1:-1]

    @recorder.use_cassette('rap_ncstream_last_index')
    def test_last_index(self):
        subset = self.var[..., 2]
        assert subset.shape == self.var.shape[:-1]

    @recorder.use_cassette('rap_ncstream_negative_index')
    def test_negative_index(self):
        subset = self.var[0, -1]
        assert subset.shape == self.var.shape[2:]

    @recorder.use_cassette('rap_ncstream_negative_slice')
    def test_negative_slice(self):
        subset = self.var[1:-1, 1, 2]
        assert subset.shape[1:] == self.var.shape[3:]
        assert subset.shape[0] == self.var.shape[0] - 2

    @recorder.use_cassette('rap_ncstream_all_indices')
    def test_all_indices(self):
        subset = self.var[0, -1, 2, 3]
        assert subset.shape == ()

    @recorder.use_cassette('rap_ncstream_slice_to_end')
    def test_slice_to_end(self):
        subset = self.var[0, 0, :3, :]
        assert subset.shape, (3 == self.var.shape[-1])

    @recorder.use_cassette('rap_ncstream_decimation')
    def test_decimation(self):
        subset = self.var[0, 0, ::2, ::2]
        assert subset.shape, ((self.var.shape[-2] + 1)//2 == (self.var.shape[-1] + 1)//2)
