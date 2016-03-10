# Copyright (c) 2016 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from io import BytesIO
from .ncstream import read_cdmrf_messages
from ..ncss import NCSS


class CDMRemoteFeature(NCSS):
    @staticmethod
    def _parse_messages(resp):
        return read_cdmrf_messages(BytesIO(resp))

    def _get_metadata(self):
        self.metadata = self.fetch_header()
        self.variables = set(g.name for g in self.metadata.grids)

    def fetch_header(self):
        query = self.query().add_query_parameter(req='header')
        return self._parse_messages(self.get_query(query).content)[0]

    def fetch_feature_type(self):
        query = self.query().add_query_parameter(req='featureType')
        return self.get_query(query).content

    def fetch_coords(self, query):
        q = query.add_query_parameter(req='coord')
        return self._parse_messages(self.get_query(q).content)

    def get_data(self, query):
        return self._parse_messages(self.get_data_raw(query))

    def get_data_raw(self, query):
        return self.get_query(query.add_query_parameter(req='data')).content
