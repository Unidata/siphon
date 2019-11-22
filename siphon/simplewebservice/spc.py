# Copyright (c) 2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Reading Storm Prediction Center Data.

======================================
This program pulls data from the Storm Prediction
Center's data from 12/31/2011 in one day increments.
Weather events that are available are
hail, wind, and tornados.

"""

from datetime import datetime, timedelta
from io import StringIO

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
    Pulls data from the SPC archive.

    This class gets data on tornados, hail, and severe wind events.
    This will return a pandas dataframe for each of these storm events.

    """

    def __init__(self):
        """Set up the endpoint."""
        super(SPCArchive, self).__init__('https://www.spc.noaa.gov/wcm/data')

    def _get_data_raw(self):


    def storm_type_selection(self):
        """
        Split http requests based on storm type.

        Parameters
        ----------
        self:
            The date_time string attribute will be used for year identification

        Returns
        -------
        (torn/wind/hail)_reports: pandas DataFrame
            This dataframe has the data about the specific SPC data type for either one day
            or a 60+ year period based on what year is chosen.

        """
        # Place holder string 'mag' will be replaced by event type (tornado, hail or wind)
        mag = str
        # Append columns with appropriate names for the archival data.
        self.columns = ['Num', 'Year', 'Month', 'Day', 'Time', 'Time Zone',
                        'State', mag, 'Injuries', 'Fatalities', 'Property Loss',
                        'Crop Loss', 'Start Lat', 'Start Lon', 'End Lat',
                        'End Lon', 'Length (mi)', 'Width (yd)', 'Ns', 'SN', 'SG',
                        'County Code 1', 'County Code 2', 'County Code 3',
                        'County Code 4']

        if self.storm_type == 'tornado':
            torn_reports = self.tornado_selection()
            return(torn_reports)
        elif self.storm_type == 'hail':
            hail_reports = self.hail_selection()
            return(hail_reports)
        elif self.storm_type == 'wind':
            wind_reports = self.wind_selection()
            return(wind_reports)
        else:
            raise ValueError('Not a valid event type: enter either tornado, wind or hail.')

    def tornado_selection(self):
        """
        Request tornado data from 1950 until this year.

        Parameters
        ----------
        self:
            Year attributes, endpoints, and column names are all used

        Returns
        -------
        torn_reports:
            Archive of tornado reports from 1950-2017

        """
        columns = self.columns
        columns[7] = 'F-Scale'
        archive_path = 'wcm/data/1950-2017_torn.csv'
        try:
            resp = self.get_path(archive_path)
            resp.raise_for_status()
            storm_list = StringIO(resp.text)
            torn_reports = pd.read_csv(storm_list, names=columns,
                                       header=0, index_col=False,
                                       usecols=[0, 1, 2, 3, 5, 6, 7, 10, 11, 12, 13,
                                                14, 15, 16, 17, 18, 19, 20, 21, 22,
                                                23, 24, 25, 26, 27])
        except requests.exceptions.HTTPError as http_error:
            raise ValueError(http_error, 'Tornado archive url not working.')

        return(torn_reports)

    def hail_selection(self):
        """
        Request hail data from 1955 until this year.

        Parameters
        ----------
        self:
            Year attributes, endpoints, and column names are all used

        Returns
        -------
        hail_reports:
            Archive of hail reports from 1955-2017

        """
        columns = self.columns
        columns[7] = 'Size (hundredth in)'
        archive_path = 'wcm/data/1955-2017_hail.csv'
        try:
            resp = self.get_path(archive_path)
            resp.raise_for_status()
            storm_list = StringIO(resp.text)
            hail_reports = pd.read_csv(storm_list, names=columns,
                                       header=0, index_col=False,
                                       usecols=[0, 1, 2, 3, 5, 6, 7, 10, 11, 12, 13,
                                                14, 15, 16, 17, 18, 19, 20, 21, 22,
                                                23, 24, 25, 26, 27])
        except requests.exceptions.HTTPError as http_error:
            raise ValueError(http_error, 'Hail archive url not working.')

        return(hail_reports)

    def wind_selection(self):
        """
        Request wind data from 1955 until this year.

        Parameters
        ----------
        self:
            Year attributes, endpoints, and column names are all used

        Returns
        -------
        wind_reports:
            Archive of wind reports from 1955-2017

        """
        columns = self.columns
        columns[7] = 'Speed (kt)'
        archive_path = 'wcm/data/1955-2017_wind.csv'
        try:
            resp = self.get_path(archive_path)
            resp.raise_for_status()
            storm_list = StringIO(resp.text)
            wind_reports = pd.read_csv(storm_list, names=columns,
                                       header=0, index_col=False,
                                       usecols=[0, 1, 2, 3, 5, 6, 7, 10, 11, 12, 13,
                                                14, 15, 16, 17, 18, 19, 20, 21, 22,
                                                23, 24, 25, 26, 27])
        except requests.exceptions.HTTPError as http_error:
            raise ValueError(http_error, 'Wind archive url not working.')

        return(wind_reports)
