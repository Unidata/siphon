# Copyright (c) 2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Provide access to the CDMRemoteFeature endpoint on TDS."""

from io import BytesIO

from .ncstream import read_cdmrf_messages
from ..ncss import NCSS


class CDMRemoteFeature(NCSS):
    """Communicate to the CDMRemoteFeature HTTP endpoint."""

    @staticmethod
    def _parse_messages(resp):
        """Parse server responses as CDMRemoteFeature messages."""
        return read_cdmrf_messages(BytesIO(resp))

    def _get_metadata(self):
        """Get header information and store as metadata for the endpoint."""
        self.metadata = self.fetch_header()
        self.variables = {g.name for g in self.metadata.grids}

    def fetch_header(self):
        """Make a header request to the endpoint."""
        query = self.query().add_query_parameter(req='header')
        return self._parse_messages(self.get_query(query).content)[0]

    def fetch_feature_type(self):
        """Request the featureType from the endpoint."""
        query = self.query().add_query_parameter(req='featureType')
        return self.get_query(query).content

    def fetch_coords(self, query):
        """Pull down coordinate data from the endpoint."""
        q = query.add_query_parameter(req='coord')
        return self._parse_messages(self.get_query(q).content)

    def get_data(self, query):
        """Pull down data (coverages) from the endpoint."""
        return self._parse_messages(self.get_data_raw(query))

    def get_data_raw(self, query):
        """Pull down the data but don't parse."""
        return self.get_query(query.add_query_parameter(req='data')).content
