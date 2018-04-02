# Copyright (c) 2013-2018 Siphon Contributors.
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

warnings.filterwarnings('ignore', 'Pandas doesn\'t allow columns to be created', UserWarning)


class IAStateUpperAir(HTTPEndPoint):
    """Download and parse data from the Iowa State's upper air archive."""

    def __init__(self):
        """Set up endpoint."""
        super(IAStateUpperAir, self).__init__('http://mesonet.agron.iastate.edu/json')

    @classmethod
    def request_data(cls, time, site_id, **kwargs):
        """Retrieve upper air observations from Iowa State's upper air archive.

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

    def _get_data(self, time, site_id):
        """Download data from Iowa State's upper air archive.

        Parameters
        ----------
        time : datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded

        Returns
        -------
            :class:`pandas.DataFrame` containing the data

        """
        json_data = self._get_data_raw(time, site_id)
        data = {}
        for pt in json_data['profiles'][0]['profile']:
            for field in ('drct', 'dwpc', 'hght', 'pres', 'sknt', 'tmpc'):
                data.setdefault(field, []).append(np.nan if pt[field] is None else pt[field])

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

        # Calculate the u and v winds
        df['u_wind'], df['v_wind'] = get_wind_components(df['speed'],
                                                         np.deg2rad(df['direction']))

        # Drop any rows with all NaN values for T, Td, winds
        df = df.dropna(subset=('temperature', 'dewpoint', 'direction', 'speed',
                               'u_wind', 'v_wind'), how='all').reset_index(drop=True)

        df['station'] = json_data['profiles'][0]['station']
        df['time'] = datetime.strptime(json_data['profiles'][0]['valid'],
                                       '%Y-%m-%dT%H:%M:%SZ')

        # Add unit dictionary
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

    def _get_data_raw(self, time, site_id):
        r"""Download data from the Iowa State's upper air archive.

        Parameters
        ----------
        time : datetime
            Date and time for which data should be downloaded
        site_id : str
            Site id for which data should be downloaded

        Returns
        -------
        list of json data

        """
        path = ('raob.py?ts={time:%Y%m%d%H}00&station={stid}').format(time=time, stid=site_id)
        resp = self.get_path(path)
        json_data = json.loads(resp.text)

        # See if the return is valid, but has no data
        if not (json_data['profiles'] and json_data['profiles'][0]['profile']):
            raise ValueError('No data available for {time:%Y-%m-%d %HZ} '
                             'for station {stid}.'.format(time=time, stid=site_id))
        return json_data
