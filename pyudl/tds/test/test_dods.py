from datetime import date, timedelta
from pyudl.tds import get_latest_dods_url


def test_get_latest():
    yesterday = date.today() - timedelta(days=1)
    datestr = yesterday.strftime('%Y%m%d')
    baseURL = 'http://thredds.ucar.edu/thredds/catalog/nexrad/level2/KFTG/'
    url = baseURL + datestr + '/catalog.xml'
    latest_url = get_latest_dods_url(url)
    assert latest_url
