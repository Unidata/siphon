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

from datetime import datetime
from io import StringIO

import pandas as pd
import requests

from siphon.http_util import HTTPEndPoint


class SPC(HTTPEndPoint):
    """
    Pulls data from the SPC.

    This class gets data on tornados, hail, and severe wind events.
    This will return a pandas dataframe for each of these storm events.

    """

    def __init__(self, stormtype, date_time):
        """
        Create class for Storm Prediction Center (SPC) and select date, and storm type.

        SPC data sifting method is differentiated based on whether the storm is before 2012
        or not. Storms after 12/31/2011 will be found by using the specific URL for the date
        selected and finding the csv file on the SPC website.

        """
        super(SPC, self).__init__('https://www.spc.noaa.gov/')

        today = datetime.today()
        self.current_year = today.year

        self.storm_type = stormtype
        self.date_time = date_time
        self.year_string = self.date_time[0:4]
        self.month_string = self.date_time[4:6]
        self.day_string = self.date_time[6:8]

        if int(self.year_string) > 2011:
            self.storms = self.storm_type_selection()
            self.day_table = self.storms

        elif int(self.year_string) <= 2011:
            raise ValueError('The SPC fetching method does not work for dates prior to 2012.')

    def storm_type_selection(self):
        """
        Split http requests based on storm type.

        Prior to 2017, the ways in which the SPC storm data is inconsistent. In order
        to deal with this, the Urls used to find the data for a given day changes
        based on the year chosen by the user.

        Parameters
        ----------
        self:
            The date_time string attribute will be used for year identification

        Returns
        -------
        (torn/wind/hail)_reports: pandas DataFrame
            Dataframe for one days worth of storm data.

        """
        # Place holder string 'mag' will be replaced by event type (tornado, hail or wind)
        mag = str
        # Colums are different for events before and after 12/31/2011.
        self.columns = ['Time', mag, 'Location', 'County', 'State',
                        'Lat', 'Lon', 'Comment']

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
        Request tornado data from 2011 until this year.

        Parameters
        ----------
        self:
            Year attributes, endpoints, and column names are all used

        Returns
        -------
        torn_reports:
            One days worth of tornado reports

        """
        columns = self.columns
        columns[1] = 'F-Scale'
        url = 'climo/reports/{}{}{}_rpts_filtered_torn.csv'
        path = url.format(self.year_string[2: 4], self.month_string, self.day_string)
        try:
            resp = self.get_path(path)
            resp.raise_for_status()
            storm_list = StringIO(resp.text)
            torn_reports = pd.read_csv(storm_list, names=columns,
                                       header=0, index_col=False,
                                       usecols=[0, 1, 2, 3, 4, 5, 6, 7])

        except requests.exceptions.HTTPError as http_error:
            raise ValueError(http_error, 'The tornado url failed for this date.')

        return(torn_reports)

    def hail_selection(self):
        """
        Request hail data from 2012 until this year.

        Parameters
        ----------
        self:
            Year attributes, endpoints, and column names are all used

        Returns
        -------
        hail_reports:
            One days worth of hail reports

        """
        columns = self.columns
        columns[1] = 'Size (in)'
        url = 'climo/reports/{}{}{}_rpts_filtered_hail.csv'
        path = url.format(self.year_string[2:4], self.month_string, self.day_string)
        try:
            resp = self.get_path(path)
            resp.raise_for_status()
            storm_list = StringIO(resp.text)
            hail_reports = pd.read_csv(storm_list, names=columns,
                                       header=0, index_col=False,
                                       usecols=[0, 1, 2, 3, 4, 5, 6, 7])
        except requests.exceptions.HTTPError as http_error:
            raise ValueError(http_error, 'The hail url failed for this date.')

        return(hail_reports)

    def wind_selection(self):
        """
        Request wind data from 2012 until this year.

        Parameters
        ----------
        self:
            Year attributes, endpoints, and column names are all used

        Returns
        -------
        wind_reports:
            One days worth of wind reports

        """
        columns = self.columns
        columns[1] = 'Speed (kt)'
        url = 'climo/reports/{}{}{}_rpts_filtered_wind.csv'
        path = url.format(self.year_string[2:4], self.month_string, self.day_string)
        try:
            resp = self.get_path(path)
            resp.raise_for_status()
            storm_list = StringIO(resp.text)
            wind_reports = pd.read_csv(storm_list, names=columns,
                                       header=0, index_col=False,
                                       usecols=[0, 1, 2, 3, 4, 5, 6, 7])
        except requests.exceptions.HTTPError as http_error:
            raise ValueError(http_error, 'The wind url failed for this date.')

        return(wind_reports)


class SPCArchive(HTTPEndPoint):
    """
    Pulls data from the SPC archive.

    This class gets data on tornados, hail, and severe wind events.
    This will return a pandas dataframe for each of these storm events.

    """

    def __init__(self, stormtype):
        """
        Create class of Storm Prediction Center Archival Data to select storm type.

        Storms are first collected into a large pd dataframe with all SPC events of
        a selected type from 1955-2017. This archival dataframe is then returned to the user
        with storms of their choice.

        """
        super(SPCArchive, self).__init__('https://www.spc.noaa.gov/')

        self.storm_type = stormtype
        self.storms = self.storm_type_selection()

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
