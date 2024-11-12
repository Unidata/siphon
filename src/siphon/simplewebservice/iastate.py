# Copyright (c) 2013-2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Read upper air data from the IA State archives."""

from datetime import datetime
import json
import warnings

import numpy as np
import numpy.ma as ma
import pandas as pd

from .._tools import get_wind_components
from ..http_util import HTTPEndPoint


class IAStateUpperAir(HTTPEndPoint):
    """Download and parse data from the Iowa State's upper air archive."""

    def __init__(self):
        """Set up endpoint."""
        super().__init__('http://mesonet.agron.iastate.edu/json')

    @classmethod
    def request_data(cls, time, site_id, interp_nans=False, **kwargs):
        """Retrieve upper air observations from Iowa State's archive for a single station.

        Parameters
        ----------
        time : datetime.datetime
            The date and time of the desired observation.

        site_id : str
            The three letter ICAO identifier of the station for which data should be
            downloaded.

        interp_nans : bool
            Flag to interpolate temperature and dewpoint at significant wind levels,
            which will otherwise be NaNs. Default is False.

        kwargs
            Arbitrary keyword arguments to use to initialize source

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        endpoint = cls()
        df = endpoint._get_data(time, site_id, None, **kwargs)
        if interp_nans:
            df['temperature'] = df['temperature'].interpolate()
            df['dewpoint'] = df['dewpoint'].interpolate()

        return df

    @classmethod
    def request_all_data(cls, time, pressure=None, **kwargs):
        """Retrieve upper air observations from Iowa State's archive for all stations.

        Parameters
        ----------
        time : datetime.datetime
            The date and time of the desired observation.

        pressure : float, optional
            The mandatory pressure level at which to request data (in hPa). If none is given,
            all the available data in the profiles is returned.

        kwargs
            Arbitrary keyword arguments to use to initialize source

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        endpoint = cls()
        df = endpoint._get_data(time, None, pressure, **kwargs)
        return df

    def _get_data(self, time, site_id, pressure=None):
        """Download data from Iowa State's upper air archive.

        Parameters
        ----------
        time : datetime.datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded
        pressure : float, optional
            Mandatory pressure level at which to request data (in hPa).

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        json_data = self._get_data_raw(time, site_id, pressure)
        data = {}
        for profile in json_data['profiles']:
            for pt in profile['profile']:
                for field in ('drct', 'dwpc', 'hght', 'pres', 'sknt', 'tmpc'):
                    data.setdefault(field, []).append(np.nan if pt[field] is None
                                                      else pt[field])
                for field in ('station', 'valid'):
                    data.setdefault(field, []).append(np.nan if profile[field] is None
                                                      else profile[field])

        # Make sure that the first entry has a valid temperature and dewpoint
        idx = np.argmax(~(np.isnan(data['tmpc']) | np.isnan(data['dwpc'])))

        # Stuff data into a pandas dataframe
        df = pd.DataFrame()
        df['pressure'] = ma.masked_invalid(data['pres'][idx:])
        df['height'] = ma.masked_invalid(data['hght'][idx:])
        df['temperature'] = ma.masked_invalid(data['tmpc'][idx:])
        df['dewpoint'] = ma.masked_invalid(data['dwpc'][idx:])
        df['direction'] = ma.masked_invalid(data['drct'][idx:])
        df['speed'] = ma.masked_invalid(data['sknt'][idx:])
        df['station'] = data['station'][idx:]
        df['time'] = [datetime.strptime(valid, '%Y-%m-%dT%H:%M:%SZ')
                      for valid in data['valid'][idx:]]

        # Calculate the u and v winds
        df['u_wind'], df['v_wind'] = get_wind_components(df['speed'],
                                                         np.deg2rad(df['direction']))

        # Drop any rows with all NaN values for T, Td, winds
        df = df.dropna(subset=('temperature', 'dewpoint', 'direction', 'speed',
                               'u_wind', 'v_wind'), how='all').reset_index(drop=True)

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
                        'time': None}

        return df

    def _get_data_raw(self, time, site_id, pressure=None):
        r"""Download data from the Iowa State's upper air archive.

        Parameters
        ----------
        time : datetime.datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded
        pressure : float, optional
            Mandatory pressure level at which to request data (in hPa).

        Returns
        -------
        list of json data

        """
        query = {'ts': time.strftime('%Y%m%d%H00')}
        if site_id is not None:
            query['station'] = site_id
        if pressure is not None:
            query['pressure'] = pressure

        resp = self.get_path('raob.py', query)
        json_data = json.loads(resp.text)

        # See if the return is valid, but has no data
        if not (json_data['profiles'] and json_data['profiles'][0]['profile']):
            message = 'No data available '
            if time is not None:
                message += f'for {time: %Y-%m-%d %HZ} '
            if site_id is not None:
                message += f'for station {site_id}'
            if pressure is not None:
                message += f'for pressure {pressure}'
            message = message + '.'
            raise ValueError(message)
        return json_data
