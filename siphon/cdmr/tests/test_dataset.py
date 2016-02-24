# Copyright (c) 2013-2015 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from siphon.testing import get_recorder
from siphon.cdmr import Dataset
from numpy.testing import assert_almost_equal, assert_array_equal, assert_array_almost_equal
import numpy as np

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
    "Test reading opaque datatype"
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_opaques.nc')
    var = ds.variables['var'][:]
    assert var.shape == (3,)
    assert var[0] == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                      b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


@recorder.use_cassette('nc4_strings')
def test_strings():
    "Test reading an array of strings"
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_strings.nc')
    var = ds.variables['measure_for_measure_var']
    assert var.shape == (43,)
    assert var[0] == 'Washington'
    assert var[10] == 'Polk'
    assert var[-1] == ''


@recorder.use_cassette('nc4_compound_ref')
def test_struct():
    "Test reading a structured variable"
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/compound/ref_tst_compounds.nc4')
    var = ds.variables['obs'][:]
    assert var.shape == (3,)
    assert var.dtype == np.dtype([('day', 'b'), ('elev', '<i2'), ('count', '<i4'),
                                  ('relhum', '<f4'), ('time', '<f8')])
    assert_array_equal(var['day'], np.array([15, -99, 20]))
    assert_array_equal(var['elev'], np.array([2, -99, 6]))
    assert_array_equal(var['count'], np.array([1, -99, 3]))
    assert_array_almost_equal(var['relhum'], np.array([0.5, -99.0, 0.75]))
    assert_array_almost_equal(var['time'],
                              np.array([3600.01, -99.0, 5000.01], dtype=np.double))


@recorder.use_cassette('nc4_compound_ref_deflate')
def test_struct():
    "Test reading a structured variable with compression turned on"
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/compound/ref_tst_compounds.nc4')
    ds.cdmr.deflate = 4
    assert ds.variables['obs'][:] is not None


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
