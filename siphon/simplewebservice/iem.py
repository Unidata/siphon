""" Requests data from IEM """
# ASOS :
# http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=LNK&data=all&year1=2018&month1=3&day1=8&year2=2018&month2=3&day2=8&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2

import requests
import datetime

from ..http_util import create_http_session


class IemAsos:
    """
    IEM ASOS data object. Handles data collection.
    """
    def __init__(self, state, sites, startDate=None, endDate=None):
        if startDate is None:
            self.startDate = datetime.datetime.now()
            self.endDate = datetime.datetime.now()
        elif endDate is None:
            self.endDate = datetime.datetime(today)

        self.state = state
        self.sites = sites
        self.getData()
        self.parseData()

    def getData(self):
        """
        Downloads IEM ASOS data
        """
        URL = 'http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?'

        for site in self.sites:
            URL = URL + '&station=' + site

        URL = URL + '&data=all'

        URL = URL + '&year1='+str(self.startDate.year)
        URL = URL + '&month1='+str(self.startDate.month)
        URL = URL + '&day1='+str(self.startDate.day)

        URL = URL + '&year2='+str(self.endDate.year)
        URL = URL + '&month2='+str(self.endDate.month)
        URL = URL + '&day2='+str(self.endDate.day)

        URL = URL + '&tz=Etc%2FUTC&format=onlycomma&latlon=yes&direct=no&report_type=1&report_type=2'
        print(URL)
        response = create_http_session().post(URL)
        self.rawData = response.text

    def parseData(self):
        """
        Parses IEM ASOS data returned by getData method.
        """
        print(self.rawData)
