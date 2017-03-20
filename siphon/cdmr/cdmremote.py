# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from io import BytesIO

from .ncstream import read_ncstream_messages
from ..http_util import HTTPEndPoint


class CDMRemote(HTTPEndPoint):
    def __init__(self, url):
        super(CDMRemote, self).__init__(url)
        self.deflate = 0

    def _fetch(self, query):
        return read_ncstream_messages(BytesIO(self.get_query(query).content))

    def fetch_capabilities(self):
        return self.get_query(self.query().add_query_parameter(req='capabilities'))

    def fetch_cdl(self):
        return self.get_query(self.query().add_query_parameter(req='CDL'))

    def fetch_data(self, **var):
        varstr = ','.join(name + self._convert_indices(ind)
                          for name, ind in var.items())
        query = self.query().add_query_parameter(req='data', var=varstr)
        return self._fetch(query)

    def fetch_header(self):
        return self._fetch(self.query().add_query_parameter(req='header'))

    def fetch_ncml(self):
        return self.get_query(self.query().add_query_parameter(req='NcML'))

    def query(self):
        """Generate a new query for CDMRemote.

        This handles turning on compression if necessary.

        Returns
        -------
        HTTPQuery
            The created query.
        """
        q = super(CDMRemote, self).query()

        # Turn on compression if it's been set on the object
        if self.deflate:
            q.add_query_parameter(deflate=self.deflate)

        return q

    @staticmethod
    def _convert_indices(ind):
        reqs = []
        subset = False
        for i in ind:
            if isinstance(i, slice):
                if i.start is None and i.stop is None and i.step is None:
                    reqs.append(':')
                else:
                    subset = True
                    # Adjust for CDMRemote weird inclusive range
                    slice_str = str(i.start) + ':' + str(i.stop - 1)

                    # Add step if necessary
                    if i.step:
                        slice_str += ':' + str(i.step)

                    reqs.append(slice_str)
            else:
                reqs.append(str(i))
                subset = True

        return '(' + ','.join(reqs) + ')' if subset else ''
