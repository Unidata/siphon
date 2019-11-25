# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Read upper air data from the Wyoming archives."""

from datetime import datetime
from io import StringIO
import warnings

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

from .._tools import get_wind_components
from ..http_util import HTTPEndPoint

warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created", UserWarning)


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
        df = endpoint._get_data(time, site_id)
        return df

    def _get_data(self, time, site_id):
        r"""Download and parse upper air observations from an online archive.

        Parameters
        ----------
        time : datetime
            The date and time of the desired observation.

        site_id : str
            The three letter ICAO identifier of the station for which data should be
            downloaded.

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        raw_data = self._get_data_raw(time, site_id)
        soup = BeautifulSoup(raw_data, 'html.parser')
        tabular_data = StringIO(soup.find_all('pre')[0].contents[0])
        col_names = ['pressure', 'height', 'temperature', 'dewpoint', 'relative_humidity',
                     'mixing_ratio', 'direction', 'speed', 'potential_temperature',
                     'equivalent_potential_temperature', 'virtual_potential_temperature']
        df = pd.read_fwf(tabular_data, skiprows=5, names=col_names)
        df['u_wind'], df['v_wind'] = get_wind_components(df['speed'],
                                                         np.deg2rad(df['direction']))

        # Drop any rows with all NaN values for T, Td, relative humidity,
        # mixing ratio, winds, thetas.
        df = df.dropna(subset=('temperature', 'dewpoint', 'relative_humidity', 
<<<<<<< HEAD
<<<<<<< HEAD
                    'mixing_ratio', 'direction', 'speed','u_wind', 'v_wind', 
                    'equivalent_potential_temperature'), how='all').reset_index(drop=True)
=======
                               'mixing_ratio', 'direction', 'speed','u_wind', 'v_wind', 
                               'equivalent_potential_temperature'), how='all')
                               .reset_index(drop=True)
>>>>>>> f6a5d94... Improved Code Quality compliance
=======
                               'mixing_ratio', 'direction', 'speed','u_wind', 'v_wind', 
                               'equivalent_potential_temperature'), how='all')
                               .reset_index(drop=True)
>>>>>>> f6a5d94ada9ca8e6b94e65bb6bc34ea96a433ae9

        # Parse metadata
        meta_data = soup.find_all('pre')[1].contents[0]
        lines = meta_data.splitlines()

        # If the station doesn't have a name identified we need to insert a
        # record showing this for parsing to proceed.
        if 'Station number' in lines[1]:
            lines.insert(1, 'Station identifier: ')

        station = lines[1].split(':')[1].strip()
        station_number = int(lines[2].split(':')[1].strip())
        sounding_time = datetime.strptime(lines[3].split(':')[1].strip(), '%y%m%d/%H%M')
        latitude = float(lines[4].split(':')[1].strip())
        longitude = float(lines[5].split(':')[1].strip())
        elevation = float(lines[6].split(':')[1].strip())

        df['station'] = station
        df['station_number'] = station_number
        df['time'] = sounding_time
        df['latitude'] = latitude
        df['longitude'] = longitude
        df['elevation'] = elevation

        # Add unit dictionary
        df.units = {'pressure': 'hPa',
                    'height': 'meter',
                    'temperature': 'degC',
                    'dewpoint': 'degC',
                    'relative_humidity': None,
                    'mixing_ratio': None,
                    'direction': 'degrees',
                    'speed': 'knot',
                    'u_wind': 'knot',
                    'v_wind': 'knot',
                    'potential_temperature': 'kelvin',
                    'equivalent_potential_temperature': 'kelvin',
                    'virtual_potential_temperature': 'kelvin',
                    'station': None,
                    'station_number': None,
                    'time': None,
                    'latitude': 'degrees',
                    'longitude': 'degrees',
                    'elevation': 'meter'}
        return df

    def _get_data_raw(self, time, site_id):
        """Download data from the University of Wyoming's upper air archive.

        Parameters
        ----------
        time : datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded

        Returns
        -------
        text of the server response

        """
        path = ('?region=naconf&TYPE=TEXT%3ALIST'
                '&YEAR={time:%Y}&MONTH={time:%m}&FROM={time:%d%H}&TO={time:%d%H}'
                '&STNM={stid}').format(time=time, stid=site_id)

        resp = self.get_path(path)
        # See if the return is valid, but has no data
        if resp.text.find("Can't") != -1:
            raise ValueError(
                'No data available for {time:%Y-%m-%d %HZ} '
                'for station {stid}.'.format(time=time, stid=site_id))

        return resp.text