from siphon.catalog import TDSCatalog, get_latest_access_url
import os.path
import vcr

recorder = vcr.VCR(cassette_library_dir=os.path.join(os.path.dirname(__file__),
                                                     'fixtures'))


class TestCatalog(object):
    baseURL = 'http://thredds-test.unidata.ucar.edu/thredds/'

    @recorder.use_cassette('thredds-test-toplevel-catalog')
    def test_basic(self):
        url = self.baseURL + 'catalog.xml'
        cat = TDSCatalog(url)
        assert 'Forecast Model Data' in cat.catalog_refs

    @recorder.use_cassette('thredds-test-latest-gfs-0p5')
    def test_access(self):
        url = self.baseURL + 'catalog/grib/NCEP/GFS/Global_0p5deg/latest.xml'
        cat = TDSCatalog(url)
        ds = list(cat.datasets.values())[0]
        assert 'OPENDAP' in ds.access_urls


@recorder.use_cassette('latest_rap_catalog')
def test_get_latest():
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
           'grib/NCEP/RAP/CONUS_13km/catalog.xml')
    latest_url = get_latest_access_url(url, "OPENDAP")
    assert latest_url
