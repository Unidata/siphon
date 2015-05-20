import os.path
import vcr
from siphon.tds import get_latest_dods_url


@vcr.use_cassette(os.path.join(os.path.dirname(__file__), 'fixtures/latest_rap_catalog'))
def test_get_latest():
    url = ('http://thredds-test.unidata.ucar.edu/thredds/catalog/'
           'grib/NCEP/RAP/CONUS_13km/catalog.xml')
    latest_url = get_latest_dods_url(url)
    assert latest_url
