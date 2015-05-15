from siphon.tds import TDSCatalog


class TestCatalog(object):
    baseURL = 'http://thredds-test.unidata.ucar.edu/thredds/'

    def test_basic(self):
        url = self.baseURL + 'catalog.xml'
        cat = TDSCatalog(url)
        assert 'Forecast Model Data' in cat.catalogRefs

    def test_access(self):
        url = self.baseURL + 'catalog/grib/NCEP/GFS/Global_0p5deg/latest.xml'
        cat = TDSCatalog(url)
        ds = list(cat.datasets.values())[0]
        assert 'OPENDAP' in ds.accessUrls
