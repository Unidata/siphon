# Copyright (c) 2019 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test National Hurricane Center database access."""

from datetime import datetime

import numpy as np
import pytest

from siphon.simplewebservice.nhc import NHCD
from siphon.testing import get_recorder


recorder = get_recorder(__file__)


@recorder.use_cassette('nhc_database')
def test_nhc():
    """Test that we are properly parsing data from the National Hurricane Center Database."""
    nhc = NHCD()
    assert(nhc.storm_table['Name'].loc[0] == '   UNNAMED')
    assert(nhc.storm_table['Basin'].loc[0] == ' AL')
    assert(nhc.storm_table['CycloneNum'].loc[0] == 1)
    assert(nhc.storm_table['Year'].loc[0] == 1851)
    assert(nhc.storm_table['StormType'].loc[0] == ' HU')
    assert(nhc.storm_table['Filename'].loc[0] == ' al011851')


@recorder.use_cassette('nhc_storm_archive')
def test_nhc_archives():
    """Test that storm dictionaries from before current year are being sifted correctly."""
    # Perform test on Hurricane Anna from 1976
    nhc = NHCD()
    models = nhc.get_tracks(1976, ' al061976')
    nhc.model_selection_latlon(models)

    # Asserting characteristics of first forecast for Anna
    assert(nhc.storm_dictionary['forecast']['Basin'].iloc[0] == 'AL')
    assert(nhc.storm_dictionary['forecast']['CycloneNum'].iloc[0] == 6)
    assert(nhc.storm_dictionary['forecast']['WarnDT'].iloc[0] == '1976072818')
    assert(nhc.storm_dictionary['forecast']['Model'].iloc[0] == ' BCD5')
    assert(nhc.storm_dictionary['forecast']['Forecast_hour'].iloc[0] == 0)
    assert(nhc.storm_dictionary['forecast']['Lat'].iloc[0] == 28)
    assert(nhc.storm_dictionary['forecast']['Lon'].iloc[0] == -52.3)

    # Asserting dictionary characteristics of best track for Anna
    assert(nhc.storm_dictionary['best_track']['Basin'].iloc[0] == 'AL')
    assert(nhc.storm_dictionary['best_track']['CycloneNum'].iloc[0] == 6)
    assert(nhc.storm_dictionary['best_track']['WarnDT'].iloc[0] == '1976072818')
    assert(nhc.storm_dictionary['best_track']['Model'].iloc[0] == ' BEST')
    assert(nhc.storm_dictionary['best_track']['Forecast_hour'].iloc[0] == 0)
    assert(nhc.storm_dictionary['best_track']['Lat'].iloc[0] == 28)
    assert(nhc.storm_dictionary['best_track']['Lon'].iloc[0] == -52.3)

    # Asserting model table characteristics for Anna
    assert(len(nhc.model_table) == 6)
    assert(nhc.model_table[0].iloc[0]['Basin'] == 'AL')
    assert(nhc.model_table[0].iloc[0]['CycloneNum'] == 6)
    assert(nhc.model_table[0].iloc[0]['WarnDT'] == '1976073018')
    assert(nhc.model_table[0].iloc[0]['Model'] == '  A72')
    assert(nhc.model_table[0].iloc[0]['Forecast_hour'] == 12)
    assert(nhc.model_table[0].iloc[0]['Lat'] == 31.7)
    assert(nhc.model_table[0].iloc[0]['Lon'] == -35.9)


@recorder.use_cassette('nhc_storm_current_year')
def test_nhc_current_year():
    """Test that storm dictionaries for current year are being sifted correctly."""
    # Perform test on Hurricane Anna from 1976
    today = datetime.today()
    current_year = today.year
    nhc = NHCD()
    nhc.get_tracks(str(current_year), ' al01' + str(current_year))

    # Asserting characteristics of first forecast for Anna
    assert(nhc.storm_dictionary['forecast']['Basin'].iloc[0] == 'AL')
    assert(nhc.storm_dictionary['forecast']['CycloneNum'].iloc[0] == 1)
    assert(isinstance(nhc.storm_dictionary['forecast']['WarnDT'].iloc[0], str))
    assert(isinstance(nhc.storm_dictionary['forecast']['Model'].iloc[0], str))
    assert(isinstance(nhc.storm_dictionary['forecast']['Forecast_hour'].iloc[0], np.int64))
    assert(isinstance(nhc.storm_dictionary['forecast']['Lat'].iloc[0], int)
           or isinstance(nhc.storm_dictionary['forecast']['Lat'].iloc[0], float))
    assert(isinstance(nhc.storm_dictionary['forecast']['Lon'].iloc[0], int)
           or isinstance(nhc.storm_dictionary['forecast']['Lon'].iloc[0], float))

    # Asserting characteristics of best track for Anna
    assert(nhc.storm_dictionary['best_track']['Basin'].iloc[0] == 'AL')
    assert(nhc.storm_dictionary['best_track']['CycloneNum'].iloc[0] == 1)
    assert(isinstance(nhc.storm_dictionary['best_track']['WarnDT'].iloc[0], str))
    assert(isinstance(nhc.storm_dictionary['best_track']['Model'].iloc[0], str))
    assert(isinstance(nhc.storm_dictionary['best_track']['Forecast_hour'].iloc[0], np.int64))
    assert(isinstance(nhc.storm_dictionary['best_track']['Lat'].iloc[0], int)
           or isinstance(nhc.storm_dictionary['best_track']['Lat'].iloc[0], float))
    assert(isinstance(nhc.storm_dictionary['best_track']['Lon'].iloc[0], int)
           or isinstance(nhc.storm_dictionary['best_track']['Lon'].iloc[0], float))


@recorder.use_cassette('nhc_no_data')
def test_no_data_nhc():
    """Test nhc data when passed an invalid url."""
    nhc = NHCD()
    with pytest.raises(ValueError):
        nhc.get_tracks(1965, ' ab123456')
