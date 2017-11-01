# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Read upper air data from the Wyoming archives."""

from io import StringIO
import warnings

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from .._tools import get_wind_components
from ..http_util import HTTPEndPoint

warnings.filterwarnings('ignore', 'Pandas doesn\'t allow columns to be created', UserWarning)


class WyomingUpperAir(HTTPEndPoint):
    """Download and parse data from the University of Wyoming's upper air archive."""

    def __init__(self):
        """Set up endpoint."""
        super(WyomingUpperAir, self).__init__('http://weather.uwyo.edu/cgi-bin/sounding')

    @classmethod
    def request_data(cls, time, site_id, **kwargs):
        r"""Retrieve upper air observations from the Wyoming archive.

        Parameters
        ----------
        time : datetime
            The date and time of the desired observation.

        site_id : str
            The three letter ICAO identifier of the station for which data should be
            downloaded.

        kwargs
            Arbitrary keyword arguments to use to initialize source

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        endpoint = cls()
        df = endpoint._get_data(time, site_id, **kwargs)
        return df

    def _get_data(self, time, site_id, region='naconf'):
        r"""Download and parse upper air observations from an online archive.

        Parameters
        ----------
        time : datetime
            The date and time of the desired observation.

        site_id : str
            The three letter ICAO identifier of the station for which data should be
            downloaded.

        region
            Region to request data from

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        raw_data = self._get_data_raw(time, site_id, region)
        col_names = ['pressure', 'height', 'temperature', 'dewpoint', 'direction', 'speed']
        df = pd.read_fwf(raw_data, skiprows=5, usecols=[0, 1, 2, 3, 6, 7], names=col_names)
        df['u_wind'], df['v_wind'] = get_wind_components(df['speed'],
                                                         np.deg2rad(df['direction']))

        # Drop any rows with all NaN values for T, Td, winds
        df = df.dropna(subset=('temperature', 'dewpoint', 'direction', 'speed',
                               'u_wind', 'v_wind'), how='all').reset_index(drop=True)

        # Add unit dictionary
        df.units = {'pressure': 'hPa',
                    'height': 'meter',
                    'temperature': 'degC',
                    'dewpoint': 'degC',
                    'direction': 'degrees',
                    'speed': 'knot',
                    'u_wind': 'knot',
                    'v_wind': 'knot'}
        return df

    def _get_data_raw(self, time, site_id, region='naconf'):
        """Download data from the University of Wyoming's upper air archive.

        Parameters
        ----------
        time : datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded
        region : str
            The region in which the station resides. Defaults to `naconf`.

        Returns
        -------
        a file-like object from which to read the data

        """
        path = ('?region={region}&TYPE=TEXT%3ALIST'
                '&YEAR={time:%Y}&MONTH={time:%m}&FROM={time:%d%H}&TO={time:%d%H}'
                '&STNM={stid}').format(region=region, time=time, stid=site_id)

        resp = self.get_path(path)
        # See if the return is valid, but has no data
        if resp.text.find('Can\'t') != -1:
            raise ValueError(
                'No data available for {time:%Y-%m-%d %HZ} from region {region} '
                'for station {stid}.'.format(time=time, region=region,
                                             stid=site_id))

        soup = BeautifulSoup(resp.text, 'html.parser')
        return StringIO(soup.find_all('pre')[0].contents[0])
