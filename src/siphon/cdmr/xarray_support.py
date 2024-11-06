# Copyright (c) 2016,2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Implement an experimental backend for using xarray to talk to TDS over CDMRemote."""

from xarray import Variable
from xarray.backends.common import AbstractDataStore, BackendArray
from xarray.core import indexing
from xarray.core.utils import FrozenDict

from . import Dataset


class CDMArrayWrapper(BackendArray):
    """Wrap a CDMRemote variable for access by xarray."""

    def __init__(self, variable_name, datastore):
        """Initialize the wrapper."""
        self.datastore = datastore
        self.variable_name = variable_name

        array = self.get_array()
        self.shape = array.shape
        self.dtype = array.dtype

    def get_array(self):
        """Get the actual array data from CDM Remote."""
        return self.datastore.ds.variables[self.variable_name]

    def __getitem__(self, item):
        """Wrap getitem around the data."""
        with self.datastore:
            arr = self.get_array()
            return indexing.explicit_indexing_adapter(item, self.shape,
                                                      indexing.IndexingSupport.BASIC,
                                                      arr.__getitem__)


class CDMRemoteStore(AbstractDataStore):
    """Manage a store for accessing CDMRemote datasets with Siphon."""

    def __init__(self, url, deflate=None):
        """Initialize the data store."""
        self.ds = Dataset(url)
        if deflate is not None:
            self.ds.cdmr.deflate = deflate

    def open_store_variable(self, name, var):
        """Turn CDMRemote variable into something like a numpy.ndarray."""
        data = indexing.LazilyOuterIndexedArray(CDMArrayWrapper(name, self))
        return Variable(var.dimensions, data, {a: getattr(var, a) for a in var.ncattrs()})

    def get_variables(self):
        """Get the variables from underlying data set."""
        return FrozenDict((k, self.open_store_variable(k, v))
                          for k, v in self.ds.variables.items())

    def get_attrs(self):
        """Get the global attributes from underlying data set."""
        return FrozenDict((a, getattr(self.ds, a)) for a in self.ds.ncattrs())

    def get_dimensions(self):
        """Get the dimensions from underlying data set."""
        return FrozenDict((k, len(v)) for k, v in self.ds.dimensions.items())
