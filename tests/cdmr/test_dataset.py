# Copyright (c) 2014-2016 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test the operation of the Dataset class from CDMRemote."""

import numpy as np
from numpy.testing import assert_almost_equal, assert_array_almost_equal, assert_array_equal
import pytest

from siphon.cdmr import Dataset
from siphon.testing import get_recorder

recorder = get_recorder(__file__)


def get_fixed_url():
    """Return a fixed URL for testing."""
    return ('http://thredds-dev.unidata.ucar.edu/thredds/cdmremote/'
            'grib/NCEP/RAP/CONUS_13km/RR_CONUS_13km_20150518_1200.grib2/GC')


class TestDataset:
    """Test basic Dataset functionality."""

    @classmethod
    def setup_class(cls):
        """Set up all tests to use the same url."""
        with recorder.use_cassette('rap_ncstream_header'):
            cls.ds = Dataset(get_fixed_url())

    def test_str_attr(self):
        """Test that we properly read a string attribute."""
        assert self.ds.Conventions == 'CF-1.6'
        assert hasattr(self.ds, 'Conventions')

    def test_dataset(self):
        """Test handling of global attributes."""
        assert hasattr(self.ds, 'Conventions')
        assert 'featureType' in self.ds.ncattrs()

    def test_variable(self):
        """Test presence of variables."""
        assert 'Temperature_isobaric' in self.ds.variables
        assert 'Convective_available_potential_energy_surface' in self.ds.variables

    def test_header_var_data_shape(self):
        """Test that variable data present in header is given proper shape."""
        assert self.ds.variables['height_above_ground_layer1_bounds'].shape == (1, 2)
        assert self.ds.variables['height_above_ground_layer1_bounds'][:].shape == (1, 2)

    @recorder.use_cassette('rap_ncstream_var')
    def test_variable_attrs(self):
        """Test that attributes are assigned properly to variables."""
        var = self.ds.variables['Temperature_isobaric']
        assert hasattr(var, 'units')
        assert 'long_name' in var.ncattrs()

    def test_var_group(self):
        """Test that Variables have correct group pointer."""
        var = self.ds.variables['Temperature_isobaric']
        assert var.group() is self.ds

    def test_dims(self):
        """Test that Dimensions have correct properties."""
        dim = self.ds.dimensions['x']
        assert dim.group() is self.ds
        assert not dim.isunlimited()


@recorder.use_cassette('rap_compressed')
def test_compression():
    """Test that compressed returns are handled."""
    ds = Dataset(get_fixed_url())
    var = ds.variables['Temperature_isobaric']
    subset = var[0, 0]
    assert subset.shape == var.shape[2:]
    assert_almost_equal(subset[0, 0], 206.65640259, 6)


@recorder.use_cassette('tds5_basic')
def test_tds5_basic():
    """Test basic handling of getting data from TDS 5."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/nc4_sfc_pres_temp.nc')
    temp = ds.variables['temperature']
    temp_data = temp[:]
    assert temp_data.shape == (6, 12)
    assert_almost_equal(temp_data[0, 0], 9.)

    temp_sub = temp[:2, :2]
    assert temp_sub.shape == (2, 2)
    assert_array_almost_equal(temp_sub,
                              np.array([[9., 10.5], [9.25, 10.75]], dtype=np.float32))


@recorder.use_cassette('tds5_empty_att')
def test_tds5_empty_atts():
    """Test handling of empty attributes."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/testEmptyAtts.nc')
    assert ds.testShortArray0 is None


@recorder.use_cassette('tds5_unsigned')
def test_tds5_unsigned():
    """Test handling of unsigned variables coming from TDS5."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/test_atomic_types.nc')
    var = ds.variables['vu64']
    assert var[:] == 18446744073709551615


@recorder.use_cassette('tds5_vlen')
def test_tds5_attr():
    """Test handling TDS 5's new attributes."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/vlen/tst_vl.nc4')
    var = ds.variables['var']
    assert var._ChunkSizes == 3


@recorder.use_cassette('tds5_vlen')
def test_tds5_vlen():
    """Test handling TDS 5's new vlen."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/vlen/tst_vl.nc4')
    dat = ds.variables['var'][:]
    assert dat.size == 3
    assert_array_equal(dat[0], np.array([-99], dtype=np.int32))
    assert_array_equal(dat[1], np.array([-99, -99], dtype=np.int32))
    assert_array_equal(dat[2], np.array([-99, -99, -99], dtype=np.int32))


@recorder.use_cassette('tds5_vlen_slicing')
def test_tds5_vlen_slicing():
    """Test handling TDS 5's new vlen and asking for indices."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/vlen/tst_vl.nc4')
    var = ds.variables['var']
    assert_array_equal(var[0], np.array([-99], dtype=np.int32))
    assert_array_equal(var[1], np.array([-99, -99], dtype=np.int32))
    assert_array_equal(var[2], np.array([-99, -99, -99], dtype=np.int32))


@recorder.use_cassette('tds5_strings')
def test_tds5_strings():
    """Test reading an array of strings."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_strings.nc')
    var = ds.variables['measure_for_measure_var']
    assert var.shape == (43,)
    assert var[0] == 'Washington'
    assert var[10] == 'Polk'
    assert var[-1] == ''


@recorder.use_cassette('tds5_opaque')
def test_tds5_opaque():
    """Test reading opaque datatype on TDS 5."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_opaques.nc')
    var = ds.variables['var'][:]
    assert var.shape == (3,)
    assert var[0] == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                      b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


@recorder.use_cassette('tds5_compound_ref')
def test_tds5_struct():
    """Test reading a structured variable in tds 5."""
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


@recorder.use_cassette('tds5_nested_structure_scalar')
def test_tds5_scalar_nested_struct():
    """Test handling a scalar nested structure on TDS 5."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/testNestedStructure.nc')
    var = ds.variables['x']
    data = var[:]
    assert data['field1']['x'] == 1


@recorder.use_cassette('nc4_enum')
def test_enum():
    """Test reading enumerated types."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/test_enum_type.nc')
    var = ds.variables['primary_cloud'][:]
    assert var[0] == 0
    assert var[1] == 2
    assert var[2] == 0
    assert var[3] == 1
    assert var[4] == 255


@recorder.use_cassette('nc4_enum')
def test_enum_ds_str():
    """Test converting a dataset with an enum to a str."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/test_enum_type.nc')
    s = str(ds)
    assert s == ('http://localhost:8080/thredds/cdmremote/nc4/tst/test_enum_type.nc\n'
                 "Dimensions:\n<class 'siphon.cdmr.dataset.Dimension'> name = station, "
                 'size = 5\nTypes:\ncloud_class_t [<cloud_class_t.Clear: 0>, '
                 '<cloud_class_t.Cumulonimbus: 1>, <cloud_class_t.Stratus: 2>, '
                 '<cloud_class_t.Stratocumulus: 3>, <cloud_class_t.Cumulus: 4>, '
                 '<cloud_class_t.Altostratus: 5>, <cloud_class_t.Nimbostratus: 6>, '
                 '<cloud_class_t.Altocumulus: 7>, <cloud_class_t.Cirrostratus: 8>, '
                 '<cloud_class_t.Cirrocumulus: 9>, <cloud_class_t.Cirrus: 10>, '
                 '<cloud_class_t.Missing: 255>]\nVariables:\n'
                 "<class 'siphon.cdmr.dataset.Variable'>\ncloud_class_t primary_cloud(station)"
                 '\n\t_FillValue: Missing\nshape = 5')


@recorder.use_cassette('nc4_opaque')
def test_opaque():
    """Test reading opaque datatype."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_opaques.nc')
    var = ds.variables['var'][:]
    assert var.shape == (3,)
    assert var[0] == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                      b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


@recorder.use_cassette('nc4_strings')
def test_strings():
    """Test reading an array of strings."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_strings.nc')
    var = ds.variables['measure_for_measure_var']
    assert var.shape == (43,)
    assert var[0] == 'Washington'
    assert var[10] == 'Polk'
    assert var[-1] == ''


@recorder.use_cassette('nc4_strings')
def test_dim_len():
    """Test getting a dimension's length."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_strings.nc')
    dim = ds.dimensions['line']
    assert len(dim) == 43


@recorder.use_cassette('nc4_vlen')
def test_vlen():
    """Test reading vlen."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/vlen/tst_vl.nc4')
    dat = ds.variables['var'][:]

    assert dat.shape == (3,)
    assert_array_equal(dat[0], np.array([-99], dtype=np.int32))
    assert_array_equal(dat[1], np.array([-99, -99], dtype=np.int32))
    assert_array_equal(dat[2], np.array([-99, -99, -99], dtype=np.int32))


@recorder.use_cassette('nc4_compound_ref')
def test_struct():
    """Test reading a structured variable."""
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
def test_struct_deflate():
    """Test reading a structured variable with compression turned on."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/compound/ref_tst_compounds.nc4')
    ds.cdmr.deflate = 4
    assert ds.variables['obs'][:] is not None


@recorder.use_cassette('nc4_groups')
def test_groups():
    """Test that a variable's path includes any parent groups."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_groups.nc')
    var = ds.groups['g1'].variables['var']

    # Need to check actual path because sample file's header includes data--no request
    # necessary
    assert var.path == '/g1/var'

    dat = var[:]
    assert dat.shape == (1,)
    assert_almost_equal(dat[0], 1.0)


@recorder.use_cassette('nc4_chararray')
def test_char():
    """Test processing arrays of characters."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/chararr.nc')
    dat = ds.variables['ca'][:]
    assert dat.size == 10
    assert dat[0] == b's'


@recorder.use_cassette('nc4_nested_structure_scalar')
def test_scalar():
    """Test handling a scalar variable."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/testNestedStructure.nc')
    var = ds.variables['x']
    data = var[:]
    assert data['field1']['x'] == 1


@recorder.use_cassette('nc4_unsigned')
def test_unsigned_var():
    """Test handling of unsigned variables."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/test_atomic_types.nc')
    var = ds.variables['vu64']
    assert var[:] == 18446744073709551615


@recorder.use_cassette('nc4_groups')
@pytest.mark.parametrize('func', [str, repr])
def test_print(func):
    """Test that str and repr of a dataset work."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/tst_groups.nc')
    s = func(ds)
    truth = """http://localhost:8080/thredds/cdmremote/nc4/tst/tst_groups.nc
Groups:
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


@recorder.use_cassette('tds5_basic')
def test_var_print():
    """Test that __str__ on var works."""
    ds = Dataset('http://localhost:8080/thredds/cdmremote/nc4/tst/nc4_sfc_pres_temp.nc')
    temp = ds.variables['temperature']
    s = str(temp)
    truth = ("<class 'siphon.cdmr.dataset.Variable'>\nfloat32 temperature(latitude, longitude)"
             '\n\tunits: celsius\n\t_ChunkSizes: [ 6 12]\nshape = (6, 12)')
    assert s == truth


class TestIndexing:
    """Test indexing on a variable makes the correct request."""

    @classmethod
    def setup_class(cls):
        """Set up tests to point to a common variable."""
        with recorder.use_cassette('rap_ncstream_header'):
            url = get_fixed_url()
            ds = Dataset(url)
            cls.var = ds.variables['Temperature_isobaric']

    @recorder.use_cassette('rap_ncstream_slices')
    def test_slices(self):
        """Test slicing."""
        subset = self.var[1:2, 1:3, 4:7, 8:12]
        assert subset.shape == (1, 2, 3, 4)

    @recorder.use_cassette('rap_ncstream_first_index')
    def test_first_index(self):
        """Test indexing leading dimensions."""
        subset = self.var[5, 10]
        assert subset.shape == self.var.shape[2:]

    @recorder.use_cassette('rap_ncstream_ellipsis_middle')
    def test_ellipsis_middle(self):
        """Test indexing with a ellipsis in the middle."""
        subset = self.var[2, ..., 3]
        assert subset.shape == self.var.shape[1:-1]

    @recorder.use_cassette('rap_ncstream_last_index')
    def test_last_index(self):
        """Test indexing the last dimension."""
        subset = self.var[..., 2]
        assert subset.shape == self.var.shape[:-1]

    @recorder.use_cassette('rap_ncstream_negative_index')
    def test_negative_index(self):
        """Test using a negative index."""
        subset = self.var[0, -1]
        assert subset.shape == self.var.shape[2:]

    @recorder.use_cassette('rap_ncstream_negative_slice')
    def test_negative_slice(self):
        """Test slicing with a negative index."""
        subset = self.var[1:-1, 1, 2]
        assert subset.shape[1:] == self.var.shape[3:]
        assert subset.shape[0] == self.var.shape[0] - 2

    @recorder.use_cassette('rap_ncstream_all_indices')
    def test_all_indices(self):
        """Test a request with an index for all dimensions."""
        subset = self.var[0, -1, 2, 3]
        assert subset.shape == ()

    @recorder.use_cassette('rap_ncstream_slice_to_end')
    def test_slice_to_end(self):
        """Test slicing to the end of a dimension."""
        subset = self.var[0, 0, :3, :]
        assert subset.shape, (self.var.shape[-1] == 3)

    @recorder.use_cassette('rap_ncstream_slice_beyond_end')
    def test_slices_long(self):
        """Test that we can use slices that go beyond last index."""
        subset = self.var[0, 0, :3, 0:1200]
        assert subset.shape == (3, self.var.shape[-1])

    @recorder.use_cassette('rap_ncstream_decimation')
    def test_decimation(self):
        """Test slices with strides."""
        subset = self.var[0, 0, ::2, ::2]
        assert subset.shape == ((self.var.shape[-2] + 1) // 2, (self.var.shape[-1] + 1) // 2)
