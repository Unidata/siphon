from datetime import datetime
from io import StringIO
import warnings, sys

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

from ..http_util import HTTPEndPoint

warnings.simplefilter("ignore")

class MesoWest(HTTPEndPoint):
    """Download and parse data from the University of Utah's MesoWest archive."""
    def __init__(self):
        """Set up endpoint."""
        super(MesoWest, self).__init__('https://mesowest.utah.edu/cgi-bin/droman/')

    @classmethod
    def request_data(cls, date, site_id, **kwargs):
        r"""Retrieve upper air observations from the University of Utah MesoWest archive.

        Parameters
        ----------
        date : datetime
            The date of the desired observation.

        site_id : str
            The four letter MesoWest identifier of the station for which data should be
            downloaded.
            https://mesowest.utah.edu/cgi-bin/droman/meso_station.cgi?area=1

        kwargs
            Arbitrary keyword arguments to use to initialize source

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        endpoint = cls()
        df = endpoint._get_data(date, site_id)
        return df

    def _get_data(self, date, site_id):
        """Download and parse upper air observations from an online archive.

        Parameters
        ----------
        date : datetime
            The date of the desired observation.

        site_id : str
            The four letter MesoWest identifier of the station for which data should be
            downloaded.
            https://mesowest.utah.edu/cgi-bin/droman/meso_station.cgi?area=1

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        raw_data = self._get_data_raw(date, site_id)
        soup = BeautifulSoup(raw_data, 'html.parser')

        names = pd.DataFrame.from_records([[td.find_next(text=True).strip('\n\t\t') for td in tr.find_all('small')] for tr in soup.find_all('th')])[1].dropna(how='any', axis=0).reset_index(drop=True)
        df = pd.DataFrame.from_records([[td.find_next(text=True).strip("\n\t\t") for td in tr.find_all("td")] for tr in soup.find_all('tr')]).dropna(how='any', axis=0).reset_index(drop=True)
        df = df.replace(r'^\s*$', np.nan, regex=True).replace('N/A', np.inf)

        df[0] = pd.to_datetime(df[0]).apply(lambda x: x.time())

        name = []
        for i in range(1, len(df.columns)):
            if str(df[i].dtypes) == 'object':
                if str(df[i].iloc[0]).replace(' ', '').isalpha():
                    pass
                else:
                    for j in range(0, len(df)):
                        if '<' in str(df[i].iloc[j]).replace(' ', ''):
                            pass
                        elif '>' in str(df[i].iloc[j]).replace(' ', ''):
                            pass
                        else:
                            df[i].iloc[j] = float(df[i].iloc[j])
            else:
                pass
            if names.tolist()[len(df.columns) + i - 1] != "":
                name.append(names.tolist()[i] + " " + names.tolist()[len(df.columns)+i - 1])
            else:
                name.append(names.tolist()[i])

        name.insert(0, names.tolist()[0])
        df = df.replace(np.inf, 'N/A')
        df.columns = [(x.lower()).replace(" ", "_") for x in name]
        return df

    def _get_data_raw(self, date, site_id):
        """Download data from the University of Utah's MesoWest archive.

        Parameters
        ----------
        date: datetime
            Date for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded
            https://mesowest.utah.edu/cgi-bin/droman/meso_station.cgi?area=1

        Returns
        -------
        text of the server response

        """
        path = ('meso_table_mesowest.cgi?stn={stid}'
                '&unit=0&time=LOCAL'
                '&day1={date:%d}&month1={date:%m}&year1={date:%Y}&hour1={date:%H}'
                '&graph=0&past=1').format(date=date, stid=site_id)
        resp = self.get_path(path)
        # See if the return is valid, but has no data
        if resp.text.find("Can't") != -1:
            raise ValueError(
                'No data available for {date:%Y-%m-%d %HZ} '
                'for station {stid}.'.format(date=date, stid=site_id))
        return resp.text
