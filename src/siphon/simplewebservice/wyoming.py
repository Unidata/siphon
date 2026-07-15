# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Read upper air data from the Wyoming archives."""

from io import StringIO
import warnings

import numpy as np
import pandas as pd
import requests

from .._tools import get_wind_components
from ..http_util import HTTPEndPoint


class WyomingUpperAir(HTTPEndPoint):
    """Download and parse data from the University of Wyoming's upper air archive."""

    def __init__(self):
        """Set up endpoint."""
        super().__init__('http://weather.uwyo.edu/wsgi')

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

        # Parse CSV. skipinitialspace is used to handle missing data being encoded by just
        # having spaces in the field
        df = pd.read_csv(StringIO(raw_data), parse_dates=['time'],
                         date_format='%Y-%m-%d %H:%M:%S', skipinitialspace=True,
                         na_values={'latitude':'-99.9900', 'longitude':'-99.9900'})
        df = df.rename(columns=lambda c: c.split('_')[0])
        df = df.rename(columns=lambda c: c.replace(' ', '_'))
        df = df.rename(columns={'geopotential_height': 'height',
                                'dew_point_temperature': 'dewpoint',
                                'wind_direction': 'direction', 'wind_speed': 'speed'})

        # Drop any rows with all NaN values for T, Td, winds
        df = df.dropna(subset=('temperature', 'dewpoint', 'direction', 'speed'),
                       how='all').reset_index(drop=True)

        df['u_wind'], df['v_wind'] = get_wind_components(df['speed'],
                                                         np.deg2rad(df['direction']))
        df['station'] = site_id
        df['height'] = df['height'].astype('float')

        # Add unit dictionary
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = {'pressure': 'hPa',
                        'height': 'meter',
                        'temperature': 'degC',
                        'dewpoint': 'degC',
                        'direction': 'degrees',
                        'speed': 'm/s',
                        'u_wind': 'm/s',
                        'v_wind': 'm/s',
                        'station': None,
                        'time': None,
                        'latitude': 'degrees',
                        'longitude': 'degrees'}

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
        path = f'sounding?type=TEXT%3ACSV&datetime={time:%Y-%m-%d %H:%M:%S}&id={site_id}'
        if recalc:
            path += '&REPLOT=1'

        try:
            return self.get_path(path).text
        except requests.HTTPError as e:
            raise ValueError from e
