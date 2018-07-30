# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Read data from the National Data Buoy Center."""

from io import StringIO
import warnings

import pandas as pd

from ..http_util import HTTPEndPoint

warnings.filterwarnings('ignore', 'Pandas doesn\'t allow columns to be created', UserWarning)


class NDBC(HTTPEndPoint):
    """Download and parse data from the National Data Buoy Center."""

    def __init__(self):
        """Set up endpoint."""
        super(NDBC, self).__init__('https://www.ndbc.noaa.gov/')

    @classmethod
    def latest_observations(cls):
        """Retrieve the latest observations for all buoys from NDBC.

        Returns
        -------
            :class:`pandas.DataFrame` containing the data
        """
        endpoint = cls()
        col_names = ['station', 'latitude', 'longitude',
                     'year', 'month', 'day', 'hour', 'minute',
                     'wind_direction', 'wind_speed', 'wind_gust',
                     'wave_height', 'dominant_wave_period', 'average_wave_period',
                     'dominant_wave_direction', 'pressure', '3hr_pressure_tendency',
                     'air_temperature', 'water_temperature', 'dewpoint',
                     'visibility', 'water_level_above_mean']

        col_units = {'station': None,
                     'latitude': 'degrees',
                     'longitude': 'degrees',
                     'wind_direction': 'degrees',
                     'wind_speed': 'meters/second',
                     'wind_gust': 'meters/second',
                     'wave_height': 'meters',
                     'dominant_wave_period': 'seconds',
                     'average_wave_period': 'seconds',
                     'dominant_wave_direction': 'degrees',
                     'pressure': 'hPa',
                     'air_temperature': 'degC',
                     'water_temperature': 'degC',
                     'dewpoint': 'degC',
                     'visibility': 'nautical_mile',
                     '3hr_pressure_tendency': 'hPa',
                     'water_level_above_mean': 'feet',
                     'time': None}
        resp = endpoint.get_path('data/latest_obs/latest_obs.txt')

        df = pd.read_fwf(StringIO(resp.text), skiprows=2,
                         na_values='MM', names=col_names)
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        df.units = col_units
        return df
