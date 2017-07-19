# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Provide a netCDF4-like interface on top of CDMRemote and NCStream."""

from __future__ import print_function

from collections import OrderedDict
import enum
import logging

from .cdmremote import CDMRemote
from .ncstream import unpack_attribute, unpack_variable

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())  # Python 2.7 needs a handler set
log.setLevel(logging.WARNING)


class AttributeContainer(object):
    """Unpack and provide access to attributes."""

    def __init__(self):
        """Initialize the container."""
        self._attrs = []

    def ncattrs(self):
        """Return a list of all available attributes."""
        return self._attrs

    def _unpack_attrs(self, attrs):
        for att in attrs:
            name, val = unpack_attribute(att)
            self._attrs.append(name)
            setattr(self, name, val)


class Group(AttributeContainer):
    """Group together variables, attributes, and dimensions."""

    def __init__(self, parent=None):
        """Initialize a Group."""
        super(Group, self).__init__()
        self.groups = OrderedDict()
        self.variables = OrderedDict()
        self.dimensions = OrderedDict()
        self.types = OrderedDict()
        if parent:
            self.dataset = parent.dataset
        else:
            self.dataset = self

    @property
    def path(self):
        """Return the full path to the Group, including any parent Groups."""
        # If root, return '/'
        if self.dataset is self:
            return ''
        else:  # Otherwise recurse
            return self.dataset.path + '/' + self.name

    def load_from_stream(self, group):
        """Load a Group from an NCStream object."""
        self._unpack_attrs(group.atts)
        self.name = group.name

        for dim in group.dims:
            new_dim = Dimension(self, dim.name)
            self.dimensions[dim.name] = new_dim
            new_dim.load_from_stream(dim)

        for var in group.vars:
            new_var = Variable(self, var.name)
            self.variables[var.name] = new_var
            new_var.load_from_stream(var)

        for grp in group.groups:
            new_group = Group(self)
            self.groups[grp.name] = new_group
            new_group.load_from_stream(grp)

        for struct in group.structs:
            new_var = Variable(self, struct.name)
            self.variables[struct.name] = new_var
            new_var.load_from_stream(struct)

        if group.enumTypes:
            for en in group.enumTypes:
                self.types[en.name] = enum.Enum(en.name,
                                                [(typ.value, typ.code) for typ in en.map])

    def __str__(self):
        """Return a string representation of the Group and its members."""
        print_groups = []
        if self.name:
            print_groups.append(self.name)

        if self.groups:
            print_groups.append('Groups:')
            for group in self.groups.values():
                print_groups.append(str(group))
                print_groups.append(str('---end group---'))

        if self.dimensions:
            print_groups.append('Dimensions:')
            for dim in self.dimensions.values():
                print_groups.append(str(dim))

        if self.types:
            print_groups.append('Types:')
            for name, typ in self.types.items():
                print_groups.append(name + ' ' + str(list(typ)))

        if self.variables:
            print_groups.append('Variables:')
            for var in self.variables.values():
                print_groups.append(str(var))

        if self.ncattrs():
            print_groups.append('Attributes:')
            for att in self.ncattrs():
                print_groups.append('\t{}: {}'.format(att, getattr(self, att)))
        return '\n'.join(print_groups)


class Dataset(Group):
    """Abstract away access to the remote dataset."""

    def __init__(self, url):
        """Initialize the dataset."""
        super(Dataset, self).__init__()
        self.cdmr = CDMRemote(url)
        self.url = url
        self._read_header()

    def _read_header(self):
        messages = self.cdmr.fetch_header()
        if len(messages) != 1:
            log.warning('Receive %d messages for header!', len(messages))
        self._header = messages[0]
        self.load_from_stream(self._header.root)

    def __str__(self):
        """Return a string representation of the Dataset and all contained members."""
        return self.url + '\n' + super(Dataset, self).__str__()


class Variable(AttributeContainer):
    """Hold information about a data variable and provide access to the underlying data."""

    def __init__(self, group, name):
        """Initialize the Variable."""
        super(Variable, self).__init__()
        self._group = group
        self.name = name
        self.dimensions = ()
        self._data = None
        self.dataset = group.dataset
        self._enum = False

    def group(self):
        """Return the parent Group."""
        return self._group

    @property
    def path(self):
        """Return the full path to the Variable, including any parent Groups."""
        return self._group.path + '/' + self.name

    def __getitem__(self, ind):
        """Access the Variable's underlying data."""
        if self._data is not None:
            # For scalars, don't slice
            return self._data if not self.shape else self._data[ind]
        else:
            ind, keep_dims = self._process_indices(ind)

            # Get the data for our request. We assume we only get 1 message.
            messages = self.dataset.cdmr.fetch_data(**{self.path: ind})
            arr = messages[0]

            # Get the proper byte ordering.
            # We handle structures by looking for a structured dtype. By convention,
            # this has a single field which is has a void type and the byte order encoded
            # in its name. This is because we can't retrieve a useful byte order from
            # any of these flexible types.
            if arr.dtype == 'O' and hasattr(arr[0], 'dtype'):
                byteorder = arr[0].dtype.byteorder
            elif arr.dtype.fields and arr.dtype.names[0] in ('>', '<'):
                byteorder = arr.dtype.names[0]
            else:
                byteorder = arr.dtype.byteorder

            # Set the dtype on the returned data to our own dtype, with byte ordering set
            # based on what was returned. This allows us to handle structures.
            dt = self.dtype.newbyteorder(byteorder)

            if arr.dtype == 'O':
                if hasattr(arr[0], 'dtype'):
                    for subarray in arr:
                        subarray.dtype = dt
            # Don't reset dtype if we've already decoded to struct
            elif arr.dtype.fields and arr.dtype.fields == dt.fields:
                pass
            else:
                arr.dtype = dt

            # Need to handle removing dimensions that have had an index
            # applied -- the protocol returns them with size 1, but numpy
            # behavior removes them
            if keep_dims:
                return arr.reshape(*[arr.shape[i] for i in keep_dims])
            else:
                return arr.squeeze()

    def _process_indices(self, ind):
        # Make sure we have a list of indices
        try:
            ind = list(ind)
        except TypeError:
            ind = [ind]

        # Make sure we don't have too many things to index
        if len(ind) > self.ndim:
            # But allow a full slice on a scalar variable
            if not (self.ndim == 0 and len(ind) == 1 and ind[0] == slice(None)):
                raise IndexError('Too many dimensions to index.')

        # Expand to a slice/ellipsis for every dimension
        if Ellipsis not in ind and len(ind) < self.ndim:
            ind.append(Ellipsis)

        # Check for ellipsis
        if Ellipsis in ind:
            num_empty = self.ndim - len(ind) + 1
            ellip_ind = ind.index(Ellipsis)
            ind.pop(ellip_ind)
            ind[ellip_ind:ellip_ind] = [slice(None)] * num_empty

        # Assemble the slices/indices
        keep_dims = []
        for dim, i in enumerate(ind):
            if isinstance(i, slice):
                is_vlen = self.dimensions and self.dimensions[dim] == '*'

                # Need to keep the dimension if we slice for non-vlen
                if not is_vlen:
                    keep_dims.append(dim)

                # Skip full slice
                if i.start is None and i.stop is None and i.step is None:
                    continue

                # vlen needs to have full slice
                if is_vlen:
                    raise RuntimeError("Can't slice along vlen dimension (%d)!", dim)

                # Adjust start and stop to handle negative indexing
                # and partial support for slicing beyond end.
                if i.start is None:
                    start = 0
                else:
                    start = self._adjust_index(dim, i.start)

                if i.stop is None:
                    stop = self.shape[dim]
                else:
                    stop = self._adjust_index(dim, i.stop)

                # Need to create new slice for adjusted values
                ind[dim] = slice(start, stop, i.step)
            else:
                # Adjust start and stop to handle negative indexing
                ind[dim] = self._adjust_index(dim, i)

        return ind, keep_dims

    def _adjust_index(self, dim, index):
        if index < 0:
            return self.shape[dim] + index
        elif index > self.shape[dim]:
            return self.shape[dim]
        return index

    def load_from_stream(self, var):
        """Populate the Variable from an NCStream object."""
        dims = []
        for d in var.shape:
            dim = Dimension(None, d.name)
            dim.load_from_stream(d)
            dims.append(dim)

        self.dimensions = tuple(dim.name for dim in dims)
        self.shape = tuple(dim.size for dim in dims)
        self.ndim = len(var.shape)
        self._unpack_attrs(var.atts)

        data, dt, typeName = unpack_variable(var)
        if data is not None:
            data = data.reshape(self.shape)
        self._data = data
        self.dtype = dt
        self.datatype = typeName

        if hasattr(var, 'enumType') and var.enumType:
            self.datatype = var.enumType
            self._enum = True

    def __str__(self):
        """Return a string representation of the Variable."""
        groups = [str(type(self))]
        groups.append('{} {}({})'.format(self.datatype, self.name,
                                         ', '.join(self.dimensions)))
        for att in self.ncattrs():
            groups.append('\t{}: {}'.format(att, getattr(self, att)))
        if self.ndim:
            if self.ndim > 1:
                shape_str = '(' + ', '.join(str(s) for s in self.shape) + ')'
            else:
                shape_str = str(self.shape[0])
            groups.append('shape = ' + shape_str)
        return '\n'.join(groups)


class Dimension(object):
    """Hold information about dimensions shared between variables."""

    def __init__(self, group, name, size=None):
        """Initialize the Dimension."""
        self._group = group
        self.name = name

        self.size = size
        self.unlimited = False
        self.private = False
        self.vlen = False

    def group(self):
        """Return the parent Group."""
        return self._group

    def isunlimited(self):
        """Return whether the dimesion is unlimited."""
        return self.unlimited

    def load_from_stream(self, dim):
        """Load from an NCStream object."""
        self.unlimited = dim.isUnlimited
        self.private = dim.isPrivate
        self.vlen = dim.isVlen
        if not self.vlen:
            self.size = dim.length

    def __len__(self):
        """Return the length of the Dimension."""
        return self.size if self.size is not None else 0

    def __str__(self):
        """Return a string representation of the Dimension information."""
        grps = ['{} '.format(type(self))]
        if self.unlimited:
            grps.append('(unlimited): ')

        if self.private:
            grps.append('(private)')
        else:
            grps.append('name = ' + self.name)

        if self.vlen:
            grps.append(', (vlen)')
        else:
            grps.append(', size = {0}'.format(self.size))

        return ''.join(grps)
