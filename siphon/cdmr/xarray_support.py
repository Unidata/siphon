# Copyright (c) 2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Implement an experimental backend for using xarray to talk to TDS over CDMRemote."""

from xarray import Variable
from xarray.backends.common import AbstractDataStore
from xarray.core import indexing
from xarray.core.utils import FrozenOrderedDict

from . import Dataset


class CDMRemoteStore(AbstractDataStore):
    """Manage a store for accessing CDMRemote datasets with Siphon."""

    def __init__(self, url, deflate=None):
        """Initialize the data store."""
        self.ds = Dataset(url)
        if deflate is not None:
            self.ds.cdmr.deflate = deflate

    @staticmethod
    def open_store_variable(var):
        """Turn CDMRemote variable into something like a numpy.ndarray."""
        data = indexing.LazilyIndexedArray(var)
        return Variable(var.dimensions, data, {a: getattr(var, a) for a in var.ncattrs()})

    def get_variables(self):
        """Get the variables from underlying data set."""
        return FrozenOrderedDict((k, self.open_store_variable(v))
                                 for k, v in self.ds.variables.items())

    def get_attrs(self):
        """Get the global attributes from underlying data set."""
        return FrozenOrderedDict((a, getattr(self.ds, a)) for a in self.ds.ncattrs())

    def get_dimensions(self):
        """Get the dimensions from underlying data set."""
        return FrozenOrderedDict((k, len(v)) for k, v in self.ds.dimensions.items())
