""" Requests data from IEM asos.py"""

import requests
import datetime
import pandas as pd

from io import StringIO

from ..http_util import create_http_session


class IemAsos:
    """Handles data collection of ASOS data from IEM.

    This handles the collection of ASOS data from the Iowa
    Environmental Mesonet, via their asos.py request URL.

    Attributes
    ----------
    startDate : datetime
        The starting date for the dataset
    endDate : datetime
        The ending date for the dataset
    sites : list
        Station IDs in the dataset
    data : pandas.DataFrame
        Pandas dataframe containing the IEM ASOS data

    """
    def __init__(self, sites, startDate=None, endDate=None):
        """Initialize the IemAsos object.

        Initialization will set the datetime objects and
        start the data call

        Parameters
        ----------
        sites : list
            List of station ID's to request data for
        startDate : datetime
            The start date as a datetime object
        endDate : datetime
            The end date as a datetime object
        """
        if startDate is None:
            self.startDate = datetime.datetime.now()
            self.endDate = datetime.datetime.now()
        elif endDate is None:
            self.endDate = datetime.datetime.now()
            self.startDate = startDate
        else:
            self.startDate = startDate
            self.endDate = endDate

        self.sites = sites
        self.getData()

    def getData(self):
        """ Downloads IEM ASOS data """

        # Build the URL
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

        URL = URL + '&tz=Etc%2FUTC&format=onlycomma&latlon=yes&direct=no' \
                    '&report_type=1&report_type=2'

        # Collect the data
        try:
            response = create_http_session().post(URL)
            csvData = StringIO(response.text)
        except requests.exceptions.Timeout:
            raise IemAsosException('Connection Timeout')

        # Process the data into a dataframe
        '''
        Convert the response text into a DataFrame. The index_col ensures that the first
        column isn't used as a row identifier. This prevents the station IDs from being used
        as row indices.
        '''
        df = pd.read_csv(csvData, header=0, sep=',', index_col=False)

        # Strip whitespace from the column names
        df.columns = df.columns.str.strip()

        df['valid'] = pd.to_datetime(df['valid'], format="%Y-%m-%d %H:%M:%S")

        self.data = df


class IemAsosException(Exception):
    """This class handles exceptions raised by the IemAsos class."""

    pass
