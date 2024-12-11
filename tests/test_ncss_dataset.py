# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test the parsing of the NCSS dataset.xml."""

import logging
import xml.etree.ElementTree as ET  # noqa:N814

from siphon.http_util import session_manager
from siphon.ncss_dataset import _Types, NCSSDataset
from siphon.testing import get_recorder

log = logging.getLogger('siphon.ncss_dataset')
log.setLevel(logging.WARNING)

recorder = get_recorder(__file__)

#
# tested:
#
#  attribute
#  values
#  projectionBox
#  axisRef
#  coordTransRef
#  grid
#  parameter
#  featureType
#  variable
#
#  projectionBox
#  axisRef
#  coordTransRef
#  coordTransform
#  gridSet
#  axis
#  LatLonBox
#  TimeSpan
#  AcceptList


class TestSimpleTypes:
    """Test parsing simple types from NCSS dataset.xml."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.types = _Types()

    def test_attribute_byte(self):
        """Test parsing a byte attribute."""
        xml = '<attribute name="missing_value" type="byte" value="1"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [1]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_invalid_byte(self, caplog):
        """Test parsing an invalid byte attribute."""
        xml = '<attribute name="missing_value" type="byte" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert 'Cannot convert "a" to int. Keeping type as str.' in caplog.text
        assert expected == actual

    def test_attribute_short(self):
        """Test parsing a short attribute."""
        xml = '<attribute name="missing_value" type="short" value="-999"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [-999]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_invalid_short(self, caplog):
        """Test parsing an invalid short attribute."""
        xml = '<attribute name="missing_value" type="short" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert 'Cannot convert "a" to int. Keeping type as str.' in caplog.text
        assert expected == actual

    def test_attribute_int(self):
        """Test parsing an int attribute."""
        xml = '<attribute name="missing_value" type="int" value="-999"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [-999]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_invalid_int(self, caplog):
        """Test parsing an invalid int attribute."""
        xml = '<attribute name="missing_value" type="int" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert 'Cannot convert "a" to int. Keeping type as str.' in caplog.text
        assert expected == actual

    def test_attribute_long(self):
        """Test parsing a long attribute."""
        xml = '<attribute name="missing_value" type="long" value="-999"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [-999]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_invalid_long(self, caplog):
        """Test parsing a invalid long attribute."""
        xml = '<attribute name="missing_value" type="long" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert 'Cannot convert "a" to int. Keeping type as str.' in caplog.text
        assert expected == actual

    def test_attribute_float(self):
        """Test parsing a float value attribute."""
        xml = '<attribute name="missing_value" type="float" value="-999.0"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [-999.0]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_invalid_float(self, caplog):
        """Test parsing an invalid float value attribute."""
        xml = '<attribute name="missing_value" type="float" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert 'Cannot convert "a" to float. Keeping type as str.' in caplog.text
        assert expected == actual

    def test_attribute_float_nan(self):
        """Test parsing a float nan attribute."""
        import math
        xml = '<attribute name="missing_value" type="float" value="NaN"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [float('NaN')]}
        actual = self.types.handle_attribute(element)
        assert expected.keys() == actual.keys()
        assert math.isnan(actual['missing_value'][0])
        assert math.isnan(expected['missing_value'][0])

    def test_attribute_double(self):
        """Test parsing a double attribute."""
        xml = '<attribute name="missing_value" type="double" value="-999.0"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [-999.0]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_invalid_double(self, caplog):
        """Test parsing an invalid double attribute."""
        xml = '<attribute name="missing_value" type="double" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert 'Cannot convert "a" to float. Keeping type as str.' in caplog.text
        assert expected == actual

    def test_attribute_double_nan(self):
        """Test parsing a double nan attribute."""
        import math
        xml = '<attribute name="missing_value" type="double" value="NaN"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [float('NaN')]}
        actual = self.types.handle_attribute(element)
        assert expected.keys() == actual.keys()
        assert math.isnan(actual['missing_value'][0])
        assert math.isnan(expected['missing_value'][0])

    def test_attribute_string_implicit(self):
        """Test parsing a string attribute."""
        xml = '<attribute name="long_name" value="Specified height level above ground"/>'
        element = ET.fromstring(xml)
        expected = {'long_name': 'Specified height level above ground'}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_string_explicit(self):
        """Test parsing a string attribute."""
        xml = '<attribute name="long_name" type="String" ' \
              'value="Specified height level above ground"/>'
        element = ET.fromstring(xml)
        expected = {'long_name': ['Specified height level above ground']}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_boolean_true(self):
        """Test parsing a boolean attribute."""
        xml = '<attribute name="missing_value" type="boolean" value="true"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [True]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_boolean_false(self):
        """Test parsing a boolean attribute."""
        xml = '<attribute name="missing_value" type="boolean" value="false"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': [False]}
        actual = self.types.handle_attribute(element)
        assert expected == actual

    def test_attribute_boolean_invalid(self, caplog):
        """Test parsing an invalid boolean attribute."""
        xml = '<attribute name="missing_value" type="boolean" value="a"/>'
        element = ET.fromstring(xml)
        expected = {'missing_value': ['a']}
        actual = self.types.handle_attribute(element)
        assert "Cannot convert values ['a'] to boolean. Keeping type as str." in caplog.text
        assert expected == actual

    def test_value_1(self):
        """Test parsing a float value tag."""
        xml = '<values>2.0</values>'
        element = ET.fromstring(xml)
        expected = {'values': ['2.0']}
        actual = self.types.handle_values(element)
        assert expected == actual

    def test_value_2(self):
        """Test parsing multiple floats in a value tag."""
        xml = '<values>50000.0 70000.0 85000.0</values>'
        element = ET.fromstring(xml)
        expected = {'values': ['50000.0', '70000.0', '85000.0']}
        actual = self.types.handle_values(element)
        assert expected == actual

    def test_value_3(self):
        """Test parsing multiple floats in a value tag to actual float values."""
        xml = '<values>50000.0 70000.0 85000.0</values>'
        element = ET.fromstring(xml)
        expected = {'values': [50000.0, 70000.0, 85000.0]}
        actual = self.types.handle_values(element, value_type='float')
        assert expected == actual

    def test_value_4(self):
        """Test parsing multiple ints in a value tag to actual int values."""
        xml = '<values>50000 70000 85000</values>'
        element = ET.fromstring(xml)
        expected = {'values': [50000, 70000, 85000]}
        actual = self.types.handle_values(element, value_type='int')
        assert expected == actual

    def test_value_range_inc0(self):
        """Test parsing a values tag with start, inc, n with inc of 0."""
        element = ET.fromstring('<values start="60.0" increment="0.0" npts="5"/>')
        assert self.types.handle_values(element) == {'values': [60.0, 60.0, 60.0, 60.0, 60.0]}

    def test_projection_box(self):
        """Test parsing a projection box."""
        xml = '<projectionBox>' \
              '<minx>-2959.1533203125</minx>' \
              '<maxx>2932.8466796875</maxx>' \
              '<miny>-1827.929443359375</miny>' \
              '<maxy>1808.070556640625</maxy>' \
              '</projectionBox>'
        element = ET.fromstring(xml)
        expected = {'projectionBox': {'minx': -2959.1533203125,
                                      'maxx': 2932.8466796875,
                                      'miny': -1827.929443359375,
                                      'maxy': 1808.070556640625}}
        actual = self.types.handle_projectionBox(element)
        assert expected == actual

    def test_axis_ref(self):
        """Test parsing an axis reference."""
        xml = '<axisRef name="time1"/>'
        element = ET.fromstring(xml)

        expected = 'time1'
        actual = self.types.handle_axisRef(element)
        assert expected == actual

    def test_coord_trans_ref(self):
        """Test parsing a coordinate transformation reference."""
        xml = '<coordTransRef name="LambertConformal_Projection"/>'
        element = ET.fromstring(xml)

        expected = {'coordTransRef': 'LambertConformal_Projection'}
        actual = self.types.handle_coordTransRef(element)
        assert expected == actual

    def test_grid(self):
        """Test parsing a grid tag."""
        xml = '<grid name="Temperature_isobaric" ' \
              'desc="Temperature @ Isobaric surface" ' \
              'shape="time1 isobaric3 y x" type="float">' \
              '<attribute name="units" value="K"/>' \
              '<attribute name="missing_value" type="float" value="-999.9"/>' \
              '<attribute name="Grib2_Parameter" type="int" value="0 0 0"/>' \
              '</grid>'
        element = ET.fromstring(xml)
        expected = {'name': 'Temperature_isobaric',
                    'desc': 'Temperature @ Isobaric surface',
                    'shape': 'time1 isobaric3 y x',
                    'attributes': {'units': 'K',
                                   'missing_value': [-999.9],
                                   'Grib2_Parameter': [0, 0, 0]}}
        actual = self.types.handle_grid(element)
        assert expected['attributes'] == actual['attributes']
        assert expected.pop('attributes', None) == actual.pop('attributes', None)

    def test_parameter(self):
        """Test parsing a parameter tag."""
        xml = '<parameter name="earth_radius" value="6371229.0 "/>'
        element = ET.fromstring(xml)
        expected = {'earth_radius': '6371229.0'}
        actual = self.types.handle_parameter(element)
        assert expected == actual

    def test_feature_type(self):
        """Test parsing a feature dataset tag."""
        xml = '<featureDataset type="station" ' \
              'url="/thredds/ncss/nws/metar/ncdecoded/' \
              'Metar_Station_Data_fc.cdmr"/>'
        element = ET.fromstring(xml)
        expected = {'type': 'station',
                    'url': '/thredds/ncss/nws/metar/ncdecoded/'
                           'Metar_Station_Data_fc.cdmr'}
        actual = self.types.handle_featureDataset(element)
        assert expected == actual

    def test_variable(self):
        """Test parsing variable tags."""
        xml = '<variable name="precipitation_amount_hourly" type="float">' \
              '<attribute name="long_name" ' \
              'value="Hourly precipitation amount"/>' \
              '<attribute name="standard_name" ' \
              'value="precipitation_amount"/>' \
              '<attribute name="_FillValue" type="float" value="-99999.0"/>' \
              '<attribute name="units" value=".01 inches"/>' \
              '</variable>'
        element = ET.fromstring(xml)
        expected = {'name': 'precipitation_amount_hourly',
                    'type': 'float',
                    'attributes': {'long_name': 'Hourly precipitation amount',
                                   'standard_name': 'precipitation_amount',
                                   '_FillValue': [-99999.0],
                                   'units': '.01 inches'}}
        actual = self.types.handle_variable(element)
        assert expected == actual


def test_dataset_elements_axis():
    """Test parsing an axis from a dataset element."""
    xml = '<axis name="height_above_ground" shape="1" type="float" ' \
          'axisType="Height"><attribute name="units" value="m"/>' \
          '<attribute name="long_name" ' \
          'value="Specified height level above ground"/>' \
          '<attribute name="positive" value="up"/><attribute ' \
          'name="Grib_level_type" type="int" value="103"/>' \
          '<attribute name="datum" value="ground"/>' \
          '<attribute name="_CoordinateAxisType" value="Height"/>' \
          '<attribute name="_CoordinateZisPositive" value="up"/>' \
          '<values>2.0</values></axis>'

    element = ET.fromstring(xml)
    actual = NCSSDataset(element).axes
    assert actual
    assert len(actual) == 1
    assert actual['height_above_ground']
    assert len(actual['height_above_ground']) == 4
    assert actual['height_above_ground']['attributes']
    assert len(actual['height_above_ground']['attributes']) == 8


def test_dataset_elements_grid_set():
    """Test parsing a gridSet from a dataset element."""
    xml = '<gridSet name="time1 isobaric3 y x"><projectionBox>' \
          '<minx>-2959.1533203125</minx>' \
          '<maxx>2932.8466796875</maxx>' \
          '<miny>-1827.929443359375</miny>' \
          '<maxy>1808.070556640625</maxy>' \
          '</projectionBox>' \
          '<axisRef name="time1"/>' \
          '<axisRef name="isobaric3"/>' \
          '<axisRef name="y"/>' \
          '<axisRef name="x"/>' \
          '<coordTransRef name="LambertConformal_Projection"/>' \
          '<grid name="Relative_humidity_isobaric" ' \
          'desc="Relative humidity @ Isobaric surface" ' \
          'shape="time1 isobaric3 y x" type="float">' \
          '<attribute name="long_name" ' \
          'value="Relative humidity @ Isobaric surface"/>' \
          '<attribute name="units" value="%"/>' \
          '<attribute name="abbreviation" value="RH"/>' \
          '<attribute name="missing_value" type="float" value="NaN"/>' \
          '<attribute name="grid_mapping" ' \
          'value="LambertConformal_Projection"/>' \
          '<attribute name="coordinates" ' \
          'value="reftime time1 isobaric3 y x "/>' \
          '<attribute name="Grib_Variable_Id" value="VAR_0-1-1_L100"/>' \
          '<attribute name="Grib2_Parameter" type="int" value="0 1 1"/>' \
          '<attribute name="Grib2_Parameter_Discipline" ' \
          'value="Meteorological products"/>' \
          '<attribute name="Grib2_Parameter_Category" value="Moisture"/>' \
          '<attribute name="Grib2_Parameter_Name" ' \
          'value="Relative humidity"/>' \
          '<attribute name="Grib2_Level_Type" value="Isobaric surface"/>' \
          '<attribute name="Grib2_Generating_Process_Type" ' \
          'value="Forecast"/>' \
          '</grid>' \
          '<grid name="Temperature_isobaric" ' \
          'desc="Temperature @ Isobaric surface" ' \
          'shape="time1 isobaric3 y x" type="float">' \
          '<attribute name="long_name" ' \
          'value="Temperature @ Isobaric surface"/>' \
          '<attribute name="units" value="K"/>' \
          '<attribute name="abbreviation" value="TMP"/>' \
          '<attribute name="missing_value" type="float" value="NaN"/>' \
          '<attribute name="grid_mapping" ' \
          'value="LambertConformal_Projection"/>' \
          '<attribute name="coordinates" ' \
          'value="reftime time1 isobaric3 y x "/>' \
          '<attribute name="Grib_Variable_Id" value="VAR_0-0-0_L100"/>' \
          '<attribute name="Grib2_Parameter" type="int" value="0 0 0"/>' \
          '<attribute name="Grib2_Parameter_Discipline" ' \
          'value="Meteorological products"/>' \
          '<attribute name="Grib2_Parameter_Category" ' \
          'value="Temperature"/>' \
          '<attribute name="Grib2_Parameter_Name" value="Temperature"/>' \
          '<attribute name="Grib2_Level_Type" value="Isobaric surface"/>' \
          '<attribute name="Grib2_Generating_Process_Type" ' \
          'value="Forecast"/>' \
          '</grid>' \
          '</gridSet>'
    element = ET.fromstring(xml)
    actual = NCSSDataset(element).gridsets
    assert actual
    assert len(actual) == 1
    assert actual['time1 isobaric3 y x']
    gs = actual['time1 isobaric3 y x']
    assert gs['axisRef']
    assert len(gs['axisRef']) == 4
    assert gs['coordTransRef']
    assert gs['projectionBox']
    assert len(gs['projectionBox']) == 4
    assert gs['grid']
    assert len(gs['grid']) == 2
    for grid in gs['grid']:
        assert len(gs['grid'][grid]) == 4
        assert gs['grid'][grid]['desc']
        assert gs['grid'][grid]['shape']
        assert gs['grid'][grid]['type']
        assert gs['grid'][grid]['type'] == 'float'
        assert len(gs['grid'][grid]['attributes']) == 13


def test_dataset_elements_coord_transform_valid():
    """Test parsing a coordinate transformation from a dataset element."""
    xml = '<coordTransform name="LambertConformal_Projection" ' \
          'transformType="Projection">' \
          '<parameter name="grid_mapping_name" ' \
          'value="lambert_conformal_conic"/>' \
          '<parameter name="latitude_of_projection_origin" ' \
          'value="40.0 "/>' \
          '<parameter name="longitude_of_central_meridian" ' \
          'value="262.0 "/>' \
          '<parameter name="standard_parallel" value="40.0 "/>' \
          '<parameter name="earth_radius" value="6371229.0 "/>' \
          '</coordTransform>'
    element = ET.fromstring(xml)
    actual = NCSSDataset(element).coordinate_transforms
    assert actual
    assert actual['LambertConformal_Projection']
    assert len(actual['LambertConformal_Projection']) == 2
    assert actual['LambertConformal_Projection']['transformType'] == 'Projection'
    parameters = actual['LambertConformal_Projection']['parameters']
    assert len(parameters) == 5
    expected = {'grid_mapping_name': 'lambert_conformal_conic',
                'latitude_of_projection_origin': '40.0',
                'longitude_of_central_meridian': '262.0',
                'standard_parallel': '40.0',
                'earth_radius': '6371229.0'}
    assert parameters == expected


def test_dataset_elements_lat_lon_box():
    """Test parsing a lat/lon box from a dataset element."""
    xml = '<LatLonBox>' \
          '<west>-140.1465</west>' \
          '<east>-56.1753</east>' \
          '<south>19.8791</south>' \
          '<north>49.9041</north>' \
          '</LatLonBox>'
    element = ET.fromstring(xml)
    expected = {'west': -140.1465,
                'east': -56.1753,
                'south': 19.8791,
                'north': 49.9041}
    actual = NCSSDataset(element).lat_lon_box
    assert actual
    assert expected == actual


def test_dataset_elements_time_span():
    """Test parsing a TimeSpan."""
    xml = '<TimeSpan><begin>2015-06-19T12:00:00Z</begin>' \
          '<end>2015-06-23T18:00:00Z</end></TimeSpan>'
    element = ET.fromstring(xml)
    expected = {'begin': '2015-06-19T12:00:00Z',
                'end': '2015-06-23T18:00:00Z'}
    actual = NCSSDataset(element).time_span
    assert actual
    assert expected == actual


def test_dataset_elements_accept_list():
    """Test parsing an AcceptList."""
    xml = '<AcceptList><GridAsPoint>' \
          '<accept displayName="xml">xml</accept>' \
          '<accept displayName="xml (file)">xml_file</accept>' \
          '<accept displayName="csv">csv</accept>' \
          '<accept displayName="csv (file)">csv_file</accept>' \
          '<accept displayName="netcdf">netcdf</accept>' \
          '<accept displayName="netcdf4">netcdf4</accept>' \
          '</GridAsPoint>' \
          '<Grid>' \
          '<accept displayName="netcdf">netcdf</accept>' \
          '<accept displayName="netcdf4">netcdf4</accept>' \
          '</Grid>' \
          '</AcceptList>'
    element = ET.fromstring(xml)
    expected = {'GridAsPoint': ['xml', 'xml_file',
                                'csv', 'csv_file',
                                'netcdf', 'netcdf4'],
                'Grid': ['netcdf', 'netcdf4']}
    actual = NCSSDataset(element).accept_list
    assert expected == actual


def test_dataset_elements_station_accept_list():
    """Test parsing acceptList for stations."""
    xml = '<AcceptList>' \
          '<accept displayName="csv">csv</accept>' \
          '<accept displayName="csv (file)">text/csv</accept>' \
          '<accept displayName="xml">xml</accept>' \
          '<accept displayName="xml (file)">text/xml</accept>' \
          '<accept displayName="WaterML 2.0">waterml2</accept>' \
          '<accept displayName="CF/NetCDF-3">netcdf</accept>' \
          '<accept displayName="CF/NetCDF-4">netcdf4</accept>' \
          '</AcceptList>'

    element = ET.fromstring(xml)
    expected = {'PointFeatureCollection': ['csv', 'text/csv',
                                           'xml', 'text/xml',
                                           'waterml2', 'netcdf', 'netcdf4']}
    actual = NCSSDataset(element).accept_list

    assert expected == actual


@recorder.use_cassette('Surface_Synoptic_Station_Dataset_xml')
def test_dataset_elements_full_ncss_station():
    """Test parsing the dataset from a full ncss station page."""
    url = ('http://thredds.ucar.edu/thredds/ncss/nws/synoptic/'
           'ncdecoded/Surface_Synoptic_Point_Data_fc.cdmr/dataset.xml')
    element = ET.fromstring(session_manager.urlopen(url).read())
    parsed = NCSSDataset(element)
    assert parsed


@recorder.use_cassette('GFS_Global_0p5_Grid_Dataset_xml')
def test_dataset_elements_full_ncss_grid():
    """Test parsing the dataset from a full ncss grid page."""
    url = ('http://thredds.ucar.edu/thredds/ncss/grib/NCEP/GFS/'
           'Global_0p5deg/GFS_Global_0p5deg_20150602_0000.grib2/'
           'dataset.xml')
    element = ET.fromstring(session_manager.urlopen(url).read())
    parsed = NCSSDataset(element)
    assert parsed


@recorder.use_cassette('GFS_TDS5')
def test_dataset_parsing_tds5(caplog):
    """Test parsing the dataset from TDS 5."""
    url = ('http://thredds-test.unidata.ucar.edu/thredds/ncss/grid/casestudies/irma/model/'
           'gfs/GFS_Global_0p5deg_20170903_1200.grib2/dataset.xml')
    element = ET.fromstring(session_manager.urlopen(url).read())
    NCSSDataset(element)
    assert len(caplog.records) == 0


@recorder.use_cassette('RAP_TDS5')
def test_dataset_parsing_rap_tds5(caplog):
    """Test parsing the dataset for RAP from TDS5."""
    url = ('https://thredds.ucar.edu/thredds/ncss/grid/grib/NCEP/RAP/CONUS_13km/'
           'RR_CONUS_13km_20241211_1900.grib2/dataset.xml')
    element = ET.fromstring(session_manager.urlopen(url).read())
    ds = NCSSDataset(element)
    assert len(caplog.records) == 0
    assert ds.axes['y']['shape'] == [337]
    assert ds.axes['reftime']['shape'] == [0]
