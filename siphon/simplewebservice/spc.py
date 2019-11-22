# Copyright (c) 2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Read storm reports from the Storm Prediction Center.

Facilities are here to access the daily sets of storm reports (from 2012 onward) as well
as the full, assembled SPC tornado, hail, and wind report databases.

"""

from datetime import datetime, timedelta
from io import BytesIO, StringIO
from zipfile import ZipFile

import pandas as pd
import requests

from siphon.http_util import HTTPEndPoint


class SPC(HTTPEndPoint):
    """
    Retrieve storm reports from the Storm Prediction Center.

    This class gets reports on tornadoes, hail, or severe wind events.
    This will return a `pandas.DataFrame` for each of these storm events.

    """

    def __init__(self):
        """Set up the endpoint."""
        super(SPC, self).__init__('https://www.spc.noaa.gov/climo/reports')

    @classmethod
    def get_wind_reports(cls, date_time):
        """
        Download severe wind reports for a given date.

        This only works for dates since the start of 2012.

        Parameters
        ----------
        date_time : datetime
            The date for which to fetch the reports.

        Returns
        -------
            `pandas.DataFrame` with the available wind reports.

        """
        return cls()._get_data('wind', date_time)

    @classmethod
    def get_tornado_reports(cls, date_time):
        """
        Download tornado reports for a given date.

        This only works for dates since the start of 2012.

        Parameters
        ----------
        date_time : datetime
            The date for which to fetch the reports.

        Returns
        -------
            `pandas.DataFrame` with the available tornado reports.

        """
        return cls()._get_data('torn', date_time)

    @classmethod
    def get_hail_reports(cls, date_time):
        """
        Download hail reports for a given date.

        This only works for dates since the start of 2012.

        Parameters
        ----------
        date_time : datetime
            The date for which to fetch the reports.

        Returns
        -------
            `pandas.DataFrame` with the available hail reports.

        """
        return cls()._get_data('hail', date_time)

    def _get_data(self, stormtype, date_time):
        """Parse the reports for a given type and date."""
        data = StringIO(self._get_data_raw(stormtype, date_time))

        def parse_report_time(s):
            hour = int(s[:2])
            val = datetime(date_time.year, date_time.month, date_time.day, hour, int(s[2:4]))
            if hour < 12:
                val += timedelta(days=1)
            return val

        reports = pd.read_csv(data, header=0, na_values='UNK', parse_dates=[0],
                              date_parser=parse_report_time)

        # Scale hail sizes to inches
        if 'Size' in reports:
            reports['Size'] /= 100

        return reports

    def _get_data_raw(self, stormtype, date_time):
        """Download the storm report file for a given type and date."""
        if date_time.year < 2012:
            raise ValueError('This does not work for dates prior to 2012.')

        path = '{:%y%m%d}_rpts_filtered_{}.csv'.format(date_time, stormtype)
        try:
            resp = self.get_path(path)
        except requests.exceptions.HTTPError:
            raise ValueError('Could not fetch reports of type {} for {}'.format(stormtype,
                                                                                date_time))
        return resp.text


class SPCArchive(HTTPEndPoint):
    """
    Retrieve the Storm Prediction Center storm report databases.

    This class gets the entire report databases for tornadoes, hail, and severe wind events.
    Data are returned as `pandas.DataFrame` instances.

    """

    def __init__(self):
        """Set up the endpoint."""
        super(SPCArchive, self).__init__('https://www.spc.noaa.gov/wcm/data')

    @classmethod
    def get_tornado_database(cls, filename='1950-2018_torn.csv.zip'):
        """
        Download and parse the SPC tornado database.

        This contains information for all tornadoes from 1950 to (roughly) present. This not
        a realtime database, so there is usually a lag between when a year ends and when
        updated data are available. The ``filename`` parameter is to allow pointing to
        an updated database file on the server.

        Parameters
        ----------
        filename : str
            Filename for the database file on the SPC server, optional.

        Returns
        -------
        `pandas.DataFrame` containing the entire SPC database

        """
        return cls()._get_data(filename)

    @classmethod
    def get_wind_database(cls, filename='1955-2018_wind.csv.zip'):
        """
        Download and parse the SPC wind report database.

        This contains information for all wind reports from 1950 to (roughly) present. This
        not a realtime database, so there is usually a lag between when a year ends and when
        updated data are available. The ``filename`` parameter is to allow pointing to
        an updated database file on the server.

        Parameters
        ----------
        filename : str
            Filename for the database file on the SPC server, optional.

        Returns
        -------
        `pandas.DataFrame` containing the entire SPC database

        """
        return cls()._get_data(filename)

    @classmethod
    def get_hail_database(cls, filename='1955-2018_hail.csv.zip'):
        """
        Download and parse the SPC hail report database.

        This contains information for all hail report from 1955 to (roughly) present. This not
        a realtime database, so there is usually a lag between when a year ends and when
        updated data are available. The ``filename`` parameter is to allow pointing to
        an updated database file on the server.

        Parameters
        ----------
        filename : str
            Filename for the database file on the SPC server, optional.

        Returns
        -------
        `pandas.DataFrame` containing the entire SPC database

        """
        return cls()._get_data(filename)

    def _get_data(self, path):
        if 'hail' in path:
            mag_col = 'Size'
        elif 'wind' in path:
            mag_col = 'Speed'
        else:
            mag_col = 'F-Scale'
        db = pd.read_csv(self._get_data_raw(path), index_col=False, parse_dates=[[4, 5]])
        db = db.drop(columns=['yr', 'mo', 'dy'])
        db = db.rename(columns={'date_time': 'Date', 'tz': 'Time Zone', 'st': 'State',
                                'stf': 'State FIPS', 'stn': 'State Number', 'mag': mag_col,
                                'inj': 'Injuries', 'fat': 'Fatalities',
                                'loss': 'Property Loss', 'closs': 'Crop Loss',
                                'slat': 'Start Lat', 'slon': 'Start Lon', 'elat': 'End Lat',
                                'elon': 'End Lon', 'len': 'Length (mi)', 'wid': 'Width (yd)',
                                'f1': 'County FIPS 1', 'f2': 'County FIPS 2',
                                'f3': 'County FIPS 3', 'f4': 'County FIPS 4',
                                'mt': 'Magnitude Type'})
        return db

    def _get_data_raw(self, path):
        resp = self.get_path(path)
        if path.endswith('.zip'):
            file_info = ZipFile(BytesIO(resp.content)).infolist()[0]
            return ZipFile(BytesIO(resp.content)).open(file_info)
        else:
            return StringIO(resp.text)
