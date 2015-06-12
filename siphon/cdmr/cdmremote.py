from .ncstream import read_ncstream_messages
from ..http_util import urlopen


class CDMRemote(object):
    # Create a custom url opener to add a user agent
    def __init__(self, url):
        self.url = url
        self.responseHandler = read_ncstream_messages

    def _fetch(self, url):
        return self.responseHandler(urlopen(url))

    def fetch_capabilities(self):
        url = self.query_url(req='capabilities')
        return self._fetch(url)

    def fetch_cdl(self):
        url = self.query_url(req='CDL')
        return self._fetch(url)

    def fetch_data(self, **var):
        varstr = ','.join(name + self._convert_indices(ind)
                          for name, ind in var.items())
        url = self.query_url(req='data', var=varstr)
        return self._fetch(url)

    def fetch_header(self):
        url = self.query_url(req='header')
        return self._fetch(url)

    def fetch_ncml(self):
        url = self.query_url(req='NcML')
        return self._fetch(url)

    def query_url(self, **kw):
        query = '&'.join('%s=%s' % i for i in kw.items())
        return '?'.join((self.url, query))

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
