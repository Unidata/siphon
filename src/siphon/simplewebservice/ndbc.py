# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Read data from the National Data Buoy Center."""

from io import StringIO
import warnings

import numpy as np
import pandas as pd
import requests

from ..http_util import HTTPEndPoint


class NDBC(HTTPEndPoint):
    """Download and parse data from the National Data Buoy Center."""

    def __init__(self):
        """Set up endpoint."""
        super().__init__('https://www.ndbc.noaa.gov/')

    @classmethod
    def realtime_observations(cls, buoy, data_type='txt'):
        """Retrieve the realtime buoy data from NDBC.

        Parameters
        ----------
        buoy : str
            Name of buoy
        data_type : str
            Type of data requested, must be one of
            'txt' standard meteorological data
            'drift' meteorological data from drifting buoys and limited moored buoy data
            mainly from international partners
            'cwind' continuous winds data (10 minute average)
            'spec' spectral wave summaries
            'ocean' oceanographic data
            'srad' solar radiation data
            'dart' water column height
            'supl' supplemental measurements data
            'rain' hourly rain data

        Returns
        -------
        `pandas.DataFrame`
            Parsed data

        """
        endpoint = cls()
        parsers = {'txt': endpoint._parse_met,
                   'drift': endpoint._parse_drift,
                   'cwind': endpoint._parse_cwind,
                   'spec': endpoint._parse_spec,
                   'ocean': endpoint._parse_ocean,
                   'srad': endpoint._parse_srad,
                   'dart': endpoint._parse_dart,
                   'supl': endpoint._parse_supl,
                   'rain': endpoint._parse_rain}

        if data_type not in parsers:
            raise KeyError('Data type must be txt, drift, cwind, spec, ocean, srad, dart,'
                           'supl, or rain for parsed realtime data.')

        raw_data = endpoint.raw_buoy_data(buoy, data_type=data_type)
        return parsers[data_type](raw_data)

    @staticmethod
    def _parse_met(content):
        """Parse standard meteorological data from NDBC buoys.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'wind_direction', 'wind_speed', 'wind_gust',
                     'wave_height', 'dominant_wave_period', 'average_wave_period',
                     'dominant_wave_direction', 'pressure',
                     'air_temperature', 'water_temperature', 'dewpoint',
                     'visibility', '3hr_pressure_tendency', 'water_level_above_mean']

        col_units = {'wind_direction': 'degrees',
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

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_drift(content):
        """Parse meteorological data from drifting buoys and limited moored buoy data.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour_minute',
                     'latitude', 'longitude',
                     'wind_direction', 'wind_speed', 'wind_gust',
                     'pressure', '3hr_pressure_tendency',
                     'air_temperature', 'water_temperature']

        col_units = {'latitude': 'degrees',
                     'longitude': 'degrees',
                     'wind_direction': 'degrees',
                     'wind_speed': 'meters/second',
                     'wind_gust': 'meters/second',
                     'pressure': 'hPa',
                     'air_temperature': 'degC',
                     'water_temperature': 'degC',
                     '3hr_pressure_tendency': 'hPa',
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['hour'] = np.floor(df['hour_minute'] / 100)
        df['minute'] = df['hour_minute'] - df['hour'] * 100
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour_minute', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_cwind(content):
        """Parse continuous wind data (10 minute average).

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'wind_direction', 'wind_speed', 'gust_direction',
                     'wind_gust', 'gust_time']

        col_units = {'wind_direction': 'degrees',
                     'wind_speed': 'meters/second',
                     'gust_direction': 'degrees',
                     'wind_gust': 'meters/second',
                     'gust_time': None,
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['gust_direction'] = df['gust_direction'].replace(999, np.nan)
        df['wind_gust'] = df['wind_gust'].replace(99.0, np.nan)
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df['hours'] = np.floor(df['gust_time'] / 100)
        df['minutes'] = df['gust_time'] - df['hours'] * 100
        df['hours'] = df['hours'].replace(99, np.nan)
        df['minutes'] = df['minutes'].replace(99, np.nan)
        df['gust_time'] = pd.to_datetime(df[['year', 'month', 'day', 'hours', 'minutes']],
                                         utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute',
                              'hours', 'minutes'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_spec(content):
        """Parse spectral wave summaries.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'significant_wave_height', 'swell_height',
                     'swell_period', 'wind_wave_height', 'wind_wave_period',
                     'swell_direction', 'wind_wave_direction', 'steepness',
                     'average_wave_period', 'dominant_wave_direction']

        col_units = {'significant_wave_height': 'meters',
                     'swell_height': 'meters',
                     'swell_period': 'seconds',
                     'wind_wave_height': 'meters',
                     'wind_wave_period': 'seconds',
                     'swell_direction': None,
                     'wind_wave_direction': None,
                     'steepness': None,
                     'average_wave_period': 'seconds',
                     'dominant_wave_direction': 'degrees',
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_ocean(content):
        """Parse oceanographic data.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'measurement_depth', 'ocean_temperature',
                     'conductivity', 'salinity', 'oxygen_concentration',
                     'oxygen_concentration_ppm', 'chlorophyll_concentration',
                     'turbidity', 'pH', 'Eh']

        col_units = {'measurement_depth': 'meters',
                     'ocean_temperature': 'degC',
                     'conductivity': 'milliSiemens/centimeter',
                     'salinity': 'psu',
                     'oxygen_concentration': 'percent',
                     'oxygen_concentration_ppm': 'ppm',
                     'chlorophyll_concentration': 'micrograms/liter',
                     'turbidity': 'ftu',
                     'pH': 'dimensionless',
                     'Eh': 'millivolts',
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_srad(content):
        """Parse solar radiation data.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'shortwave_radiation_licor', 'shortwave_radiation_eppley',
                     'longwave_radiation']

        col_units = {'shortwave_radiation_licor': 'watts/meter^2',
                     'shortwave_radiation_eppley': 'watts/meter^2',
                     'longwave_radiation': 'watts/meter^2',
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_dart(content):
        """Parse water column height data.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute', 'second',
                     'measurement_type', 'height']

        col_units = {'measurement_type': 'minutes',
                     'height': 'meters',
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')

        # Replace measurement type integer with minute value
        # 1 = 15-minute measurement
        # 2 = 1-minute measurement
        # 3 = 15-second measurement
        df['measurement_type'] = df['measurement_type'].replace(1, 15)
        df['measurement_type'] = df['measurement_type'].replace(2, 1)
        df['measurement_type'] = df['measurement_type'].replace(3, 0.25)

        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour',
                                        'minute', 'second']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute', 'second'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_rain(content):
        """Parse hourly rain data.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'hourly_accumulation']

        col_units = {'hourly_accumulation': 'millimeters',
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')

        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _parse_supl(content):
        """Parse supplemental measurements data.

        Parameters
        ----------
        content : str
            Data to parse

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        col_names = ['year', 'month', 'day', 'hour', 'minute',
                     'hourly_low_pressure', 'hourly_low_pressure_time',
                     'hourly_high_wind', 'hourly_high_wind_direction',
                     'hourly_high_wind_time']

        col_units = {'hourly_low_pressure': 'hPa',
                     'hourly_low_pressure_time': None,
                     'hourly_high_wind': 'meters/second',
                     'hourly_high_wind_direction': 'degrees',
                     'hourly_high_wind_time': None,
                     'time': None}

        df = pd.read_csv(StringIO(content), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')

        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)

        df['hours'] = np.floor(df['hourly_low_pressure_time'] / 100)
        df['minutes'] = df['hourly_low_pressure_time'] - df['hours'] * 100
        df['hours'] = df['hours'].replace(99, np.nan)
        df['minutes'] = df['minutes'].replace(99, np.nan)
        df['hourly_low_pressure_time'] = pd.to_datetime(df[['year', 'month', 'day', 'hours',
                                                            'minutes']], utc=True)

        df['hours'] = np.floor(df['hourly_high_wind_time'] / 100)
        df['minutes'] = df['hourly_high_wind_time'] - df['hours'] * 100
        df['hours'] = df['hours'].replace(99, np.nan)
        df['minutes'] = df['minutes'].replace(99, np.nan)
        df['hourly_high_wind_time'] = pd.to_datetime(df[['year', 'month', 'day',
                                                         'hours', 'minutes']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute', 'hours', 'minutes'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

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

        df = pd.read_csv(StringIO(resp.text), comment='#', na_values='MM',
                         names=col_names, sep=r'\s+')
        df['time'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute']], utc=True)
        df = df.drop(columns=['year', 'month', 'day', 'hour', 'minute'])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', "Pandas doesn't allow columns to be created",
                                    UserWarning)
            df.units = col_units

        return df

    @staticmethod
    def _check_if_url_valid(url):
        """Check if a url is valid (returns 200) or not.

        Parameters
        ----------
        url : str
            URL to check

        Returns
        -------
            bool if url is valid

        """
        r = requests.head(url, timeout=300)
        return r.status_code == 200

    @classmethod
    def buoy_data_types(cls, buoy):
        """Determine which types of data are available for a given buoy.

        Parameters
        ----------
        buoy : str
            Buoy name

        Returns
        -------
        dict[str, str]
            dict of valid file extensions and their descriptions

        """
        endpoint = cls()
        file_types = {'txt': 'standard meteorological data',
                      'drift': 'meteorological data from drifting buoys and limited moored'
                               'buoy data mainly from international partners',
                      'cwind': 'continuous wind data (10 minute average)',
                      'spec': 'spectral wave summaries',
                      'data_spec': 'raw spectral wave data',
                      'swdir': 'spectral wave data (alpha1)',
                      'swdir2': 'spectral wave data (alpha2)',
                      'swr1': 'spectral wave data (r1)',
                      'swr2': 'spectral wave data (r2)',
                      'adcp': 'acoustic doppler current profiler',
                      'ocean': 'oceanographic data',
                      'tide': 'tide data',
                      'srad': 'solar radiation data',
                      'dart': 'water column height',
                      'supl': 'supplemental measurements data',
                      'rain': 'hourly rain data'}
        available_data = {}
        buoy_url = 'https://www.ndbc.noaa.gov/data/realtime2/' + buoy + '.'
        for key in file_types:
            if endpoint._check_if_url_valid(buoy_url + key):
                available_data[key] = file_types[key]
        return available_data

    @classmethod
    def raw_buoy_data(cls, buoy, data_type='txt'):
        """Retrieve the raw buoy data contents from NDBC.

        Parameters
        ----------
        buoy : str
            Name of buoy

        data_type : str
            Type of data requested, must be one of
            'txt' standard meteorological data
            'drift' meteorological data from drifting buoys and limited moored buoy data
            mainly from international partners
            'cwind' continuous winds data (10 minute average)
            'spec' spectral wave summaries
            'data_spec' raw spectral wave data
            'swdir' spectral wave data (alpha1)
            'swdir2' spectral wave data (alpha2)
            'swr1' spectral wave data (r1)
            'swr2' spectral wave data (r2)
            'adcp' acoustic doppler current profiler
            'ocean' oceanographic data
            'tide' tide data
            'srad' solar radiation data
            'dart' water column height
            'supl' supplemental measurements data
            'rain' hourly rain data

        Returns
        -------
        str
            Raw data string

        """
        endpoint = cls()
        resp = endpoint.get_path(f'data/realtime2/{buoy}.{data_type}')
        return resp.text
