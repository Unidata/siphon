# Copyright (c) 2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Provide access to a TDS Coverage Dataset."""

from collections import OrderedDict
import logging
import warnings

from .cdmremotefeature import CDMRemoteFeature
from .dataset import AttributeContainer

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())  # Python 2.7 needs a handler set
log.setLevel(logging.WARNING)


def reindent_lines(new_leader, source):
    """Re-indent string lines."""
    return new_leader + ('\n' + new_leader).join(source.split('\n'))


class CoverageDataset(AttributeContainer):
    """Wrap dataset access using CDMRemoteFeature and Coverages.

    This is still experimental.
    """

    def __init__(self, url):
        """Initialize CoverageDataset from a url pointing to CDMRemoteFeature endpoint."""
        super(CoverageDataset, self).__init__()
        warnings.warn('CoverageDataset is in early development, unsupported, and API may '
                      'change at any time.')
        self.cdmrf = CDMRemoteFeature(url)
        self.name = 'Unnamed'
        self.lon_lat_domain = None
        self.proj_domain = None
        self.date_range = None
        self.type = None
        self.axes = OrderedDict()
        self.coord_systems = OrderedDict()
        self.grids = OrderedDict()
        self.transforms = OrderedDict()
        self._read_header()

    def _read_header(self):
        """Get the needed header information to initialize dataset."""
        self._header = self.cdmrf.fetch_header()
        self.load_from_stream(self._header)

    def load_from_stream(self, header):
        """Populate the CoverageDataset from the protobuf information."""
        self._unpack_attrs(header.atts)
        self.name = header.name
        self.lon_lat_domain = header.latlonRect
        self.proj_domain = header.projRect
        self.date_range = header.dateRange
        self.type = header.coverageType

        for sys in header.coordSys:
            self.coord_systems[sys.name] = sys

        for trans in header.coordTransforms:
            self.transforms[trans.name] = trans

        for ax in header.coordAxes:
            self.axes[ax.name] = ax

        for cov in header.grids:
            self.grids[cov.name] = cov

    def __str__(self):
        """Create a string representation of CoverageDataset."""
        print_groups = []
        if self.name:
            print_groups.append(self.name + ' (' + str(self.type) + ')')

        print_groups.append('Lon/Lat Domain: {0}'.format(self.lon_lat_domain))
        print_groups.append('Projected Domain: {0}'.format(self.proj_domain))
        print_groups.append('Date Range: {0}'.format(self.date_range))

        indent = ' ' * 4
        if self.axes:
            print_groups.append('Axes:')
            for ax in self.axes.values():
                print_groups.append(reindent_lines(indent, str(ax)))

        if self.coord_systems:
            print_groups.append('Coordinate Systems:')
            for sys in self.coord_systems.values():
                print_groups.append(reindent_lines(indent, str(sys)))

        if self.transforms:
            print_groups.append('Coordinate Transforms:')
            for trans in self.transforms.values():
                print_groups.append(reindent_lines(indent, str(trans)))

        if self.grids:
            print_groups.append('Grids:')
            for grid in self.grids.values():
                print_groups.append(reindent_lines(indent, str(grid)))

        if self.ncattrs():
            print_groups.append('Attributes:')
            for att in self.ncattrs():
                print_groups.append('{0}{1}: {2}'.format(indent, att, getattr(self, att)))
        return '\n'.join(print_groups)
