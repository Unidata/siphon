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


def _safe_float(s):
    """Convert to float, handling ****** as a string for missing."""
    return pd.NA if all(c == '*' for c in s) or s == '-9999.0' else float(s)


class WyomingUpperAir(HTTPEndPoint):
    """Download and parse data from the University of Wyoming's upper air archive."""

    def __init__(self):
        """Set up endpoint."""
        super().__init__('http://weather.uwyo.edu/cgi-bin/sounding')

    @classmethod
    def request_data(cls, time, site_id, recalc=False, **kwargs):
        r"""Retrieve upper air observations from the Wyoming archive.

        Parameters
        ----------
        time : datetime.datetime
            The date and time of the desired observation.

        site_id : str
            The three letter ICAO identifier of the station for which data should be
            downloaded.

        recalc : bool
            Whether to request the server recalculate the data (i.e. ignore its cache) before
            returning it. Defaults to False. NOTE: This should be used sparingly because it
            will increase the load on the service.

        kwargs
            Arbitrary keyword arguments to use to initialize source

        Returns
        -------
        `pandas.DataFrame`
            Parsed data

        """
        endpoint = cls()
        df = endpoint._get_data(time, site_id, recalc=recalc)
        return df

    def _get_data(self, time, site_id, recalc=False):
        r"""Download and parse upper air observations from an online archive.

        Parameters
        ----------
        time : datetime.datetime
            The date and time of the desired observation.

        site_id : str
            The three letter ICAO identifier of the station for which data should be
            downloaded.

        recalc : bool
            Returns recalculated data if True. Defaults to False.

        Returns
        -------
        `pandas.DataFrame`

        """
        raw_data = self._get_data_raw(time, site_id, recalc=recalc)
        soup = BeautifulSoup(raw_data, 'html.parser')
        tabular_data = StringIO(soup.find_all('pre')[0].contents[0])
        col_names = ['pressure', 'height', 'temperature', 'dewpoint', 'direction', 'speed']
        df = pd.read_fwf(tabular_data, widths=[7] * 8, skiprows=5,
                         usecols=[0, 1, 2, 3, 6, 7], names=col_names)

        df['u_wind'], df['v_wind'] = get_wind_components(df['speed'],
                                                         np.deg2rad(df['direction']))

        # Drop any rows with all NaN values for T, Td, winds
        df = df.dropna(subset=('temperature', 'dewpoint', 'direction', 'speed',
                               'u_wind', 'v_wind'), how='all').reset_index(drop=True)

        # Parse metadata
        meta_data = soup.find_all('pre')[1].contents[0]
        lines = meta_data.splitlines()

        # Convert values after table into key, value pairs using the name to the left of the :
        post_values = dict(tuple(map(str.strip, line.split(': '))) for line in lines[1:])

        station = post_values.get('Station identifier', '')
        station_number = int(post_values['Station number'])
        sounding_time = datetime.strptime(post_values['Observation time'], '%y%m%d/%H%M')
        latitude = _safe_float(post_values.get('Station latitude', '******'))
        longitude = _safe_float(post_values.get('Station longitude', '******'))
        elevation = _safe_float(post_values.get('Station elevation', '******'))
        pw = float(post_values['Precipitable water [mm] for entire sounding'])

        df['station'] = station
        df['station_number'] = station_number
        df['time'] = sounding_time
        df['latitude'] = latitude
        df['longitude'] = longitude
        df['elevation'] = elevation
        df['pw'] = pw

        # Add unit dictionary
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = {'pressure': 'hPa',
                        'height': 'meter',
                        'temperature': 'degC',
                        'dewpoint': 'degC',
                        'direction': 'degrees',
                        'speed': 'knot',
                        'u_wind': 'knot',
                        'v_wind': 'knot',
                        'station': None,
                        'station_number': None,
                        'time': None,
                        'latitude': 'degrees',
                        'longitude': 'degrees',
                        'elevation': 'meter',
                        'pw': 'millimeter'}

        return df

    def _get_data_raw(self, time, site_id, recalc=False):
        """Download data from the University of Wyoming's upper air archive.

        Parameters
        ----------
        time : datetime.datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded
        recalc : bool
            Returns recalculated data if True. Defaults to False.

        Returns
        -------
        str
            text of the server response

        """
        path = ('?region=naconf&TYPE=TEXT%3ALIST'
                f'&YEAR={time:%Y}&MONTH={time:%m}&FROM={time:%d%H}&TO={time:%d%H}'
                f'&STNM={site_id}')
        if recalc:
            path += '&REPLOT=1'

        resp = self.get_path(path)
        # See if the return is valid, but has no data
        if resp.text.find("Can't") != -1:
            raise ValueError(
                f'No data available for {time:%Y-%m-%d %HZ} '
                f'for station {site_id}.')

        return resp.text
