# Copyright (c) 2013-2015 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from __future__ import print_function
from collections import OrderedDict

from .cdmremote import CDMRemote
from .ncstream import unpack_attribute, unpack_variable


class AttributeContainer(object):
    def __init__(self):
        self._attrs = []

    def ncattrs(self):
        return self._attrs

    def _unpack_attrs(self, attrs):
        for att in attrs:
            name, val = unpack_attribute(att)
            self._attrs.append(name)
            setattr(self, name, val)


class Group(AttributeContainer):
    def __init__(self, parent=None):
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
        'The full path to the Group, including any parent Groups.'
        # If root, return '/'
        if self.dataset is self:
            return ''
        else:  # Otherwise recurse
            return self.dataset.path + '/' + self.name

    def load_from_stream(self, group):
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
                type_map = OrderedDict()
                self.types[en.name] = type_map
                for typ in en.map:
                    type_map[typ.code] = typ.value

    def __str__(self):
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
                print_groups.append(name + ' ' + typ)

        if self.variables:
            print_groups.append('Variables:')
            for var in self.variables.values():
                print_groups.append(str(var))

        if self.ncattrs():
            print_groups.append('Attributes:')
            for att in self.ncattrs():
                print_groups.append('\t%s: %s' % (att, getattr(self, att)))
        return '\n'.join(print_groups)


class Dataset(Group):
    def __init__(self, url):
        super(Dataset, self).__init__()
        self.cdmr = CDMRemote(url)
        self._read_header()

    def _read_header(self):
        messages = self.cdmr.fetch_header()
        if len(messages) != 1:
            log.warning('Receive %d messages for header!', len(messages))
        self._header = messages[0]
        self.load_from_stream(self._header.root)

    def __unicode__(self):
        return self.cdmr.url + '\n' + Group.__unicode__(self)


class Variable(AttributeContainer):
    def __init__(self, group, name):
        super(Variable, self).__init__()
        self._group = group
        self.name = name
        self.dimensions = ()
        self._data = None
        self.dataset = group.dataset
        self._enum = False

    def group(self):
        return self._group

    @property
    def path(self):
        'The full path to the Variable, including any parent Groups.'
        return self._group.path + '/' + self.name

    def __getitem__(self, ind):
        if self._data is not None:
            return self._data[ind]
        else:
            ind, keep_dims = self._process_indices(ind)
            messages = self.dataset.cdmr.fetch_data(**{self.path: ind})
            assert len(messages) == 1

            # Need to handle removing dimensions that have had an index
            # applied -- the protocol returns them with size 1, but numpy
            # behavior removes them
            arr = messages[0]
            if keep_dims:
                ret = arr.reshape(*[arr.shape[i] for i in keep_dims])
            else:
                ret = arr.squeeze()

            if self.dtype.byteorder != '|':
                old_dtype = arr.dtype
                ret.dtype = self.dtype.newbyteorder(old_dtype.byteorder)
            return ret

    def _process_indices(self, ind):
        # Make sure we have a list of indices
        try:
            ind = list(ind)
        except TypeError:
            ind = [ind]

        # Make sure we don't have too many things to index
        if len(ind) > self.ndim:
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
                # Need to keep the dimension if we slice
                keep_dims.append(dim)

                # Skip full slice
                if i.start is None and i.stop is None and i.step is None:
                    continue

                # Adjust start and stop to handle negative indexing
                # and partial support for slicing beyond end.
                if i.start is None:
                    start = 0
                else:
                    start = self.adjust_index(dim, i.start)

                if i.stop is None:
                    stop = self.shape[dim]
                else:
                    stop = self.adjust_index(dim, i.stop)

                # Need to create new slice for adjusted values
                ind[dim] = slice(start, stop, i.step)
            else:
                # Adjust start and stop to handle negative indexing
                ind[dim] = self.adjust_index(dim, i)

        return ind, keep_dims

    def adjust_index(self, dim, index):
        if index < 0:
            return self.shape[dim] + index
        elif index > self.shape[dim]:
            return self.shape[dim]
        return index

    def load_from_stream(self, var):
        data, dt, typeName = unpack_variable(var)
        self._data = data
        self.dtype = dt
        self.datatype = typeName

        self.dimensions = tuple(dim.name if dim.name else '<unnamed>'
                                for dim in var.shape)
        self.shape = tuple(dim.length for dim in var.shape)
        self.ndim = len(var.shape)
        self._unpack_attrs(var.atts)

        if hasattr(var, 'enumType') and var.enumType:
            self.datatype = var.enumType
            self._enum = True

    def __str__(self):
        groups = [str(type(self))]
        groups.append('%s %s(%s)' % (self.datatype, self.name,
                                     ', '.join(self.dimensions)))
        for att in self.ncattrs():
            groups.append('\t%s: %s' % (att, getattr(self, att)))
        if self.ndim:
            if self.ndim > 1:
                shape_str = '(' + ', '.join('%d' % s for s in self.shape) + ')'
            else:
                shape_str = '%d' % self.shape[0]
            groups.append('shape = ' + shape_str)
        return '\n'.join(groups)


class Dimension(object):
    def __init__(self, group, name, size=None):
        self._group = group
        self.name = name

        self.size = size
        self.unlimited = False
        self.private = False
        self.vlen = False

    def group(self):
        return self._group

    def isunlimited(self):
        return self.unlimited

    def load_from_stream(self, dim):
        self.size = dim.length
        self.unlimited = dim.isUnlimited
        self.private = dim.isPrivate
        self.vlen = dim.isVlen

    def __len__(self):
        return self.size

    def __str__(self):
        grps = ['%s ' % type(self)]
        if self.unlimited:
            grps.append('(unlimited): ')

        if self.private:
            grps.append('(private)')
        else:
            grps.append('name = ' + self.name)

        if self.vlen:
            grps.append(', (vlen)')
        else:
            grps.append(', size = %d' % self.size)

        return ''.join(grps)
