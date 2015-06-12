import logging
import xml.etree.ElementTree as ET

from nose.tools import assert_dict_equal, assert_equal
from siphon.ncss_dataset import NcssDataset, _Types
from siphon.testing import get_recorder
from siphon.http_util import urlopen

log = logging.getLogger("siphon.ncss_dataset")
log.setLevel(logging.WARNING)
log.addHandler(logging.StreamHandler())

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


class TestSimpleTypes(object):

    @classmethod
    def setup_class(cls):
        cls.types = _Types()

    def test_attribute_1(self):
        xml = '<attribute name="long_name" ' \
              'value="Specified height level above ground"/>'
        element = ET.fromstring(xml)
        expected = {"long_name": "Specified height level above ground"}
        actual = self.types.handle_attribute(element)
        assert_dict_equal(expected, actual)

    def test_attribute_2(self):
        import math
        xml = '<attribute name="missing_value" type="float" value="NaN"/>'
        element = ET.fromstring(xml)
        expected = {"missing_value": [float("NaN")]}
        actual = self.types.handle_attribute(element)
        assert_equal(expected.keys(), actual.keys())
        assert(math.isnan(actual["missing_value"][0]))
        assert(math.isnan(expected["missing_value"][0]))

    def test_attribute_3(self):
        xml = '<attribute name="missing_value" type="float" value="-999"/>'
        element = ET.fromstring(xml)
        expected = {"missing_value": [float(-999)]}
        actual = self.types.handle_attribute(element)
        assert_dict_equal(expected, actual)

    def test_attribute_4(self):
        xml = '<attribute name="missing_value" type="int" value="-999"/>'
        element = ET.fromstring(xml)
        expected = {"missing_value": [-999]}
        actual = self.types.handle_attribute(element)
        assert_dict_equal(expected, actual)

    def test_value_1(self):
        xml = '<values>2.0</values>'
        element = ET.fromstring(xml)
        expected = {"values": ["2.0"]}
        actual = self.types.handle_values(element)
        assert_dict_equal(expected, actual)

    def test_value_2(self):
        xml = '<values>50000.0 70000.0 85000.0</values>'
        element = ET.fromstring(xml)
        expected = {"values": ["50000.0", "70000.0", "85000.0"]}
        actual = self.types.handle_values(element)
        assert_dict_equal(expected, actual)

    def test_value_3(self):
        xml = '<values>50000.0 70000.0 85000.0</values>'
        element = ET.fromstring(xml)
        expected = {"values": [50000.0, 70000.0, 85000.0]}
        actual = self.types.handle_values(element, value_type="float")
        assert_dict_equal(expected, actual)

    def test_value_4(self):
        xml = '<values>50000 70000 85000</values>'
        element = ET.fromstring(xml)
        expected = {"values": [50000, 70000, 85000]}
        actual = self.types.handle_values(element, value_type="int")
        assert_dict_equal(expected, actual)

    def test_projection_box(self):
        xml = '<projectionBox>' \
              '<minx>-2959.1533203125</minx>' \
              '<maxx>2932.8466796875</maxx>' \
              '<miny>-1827.929443359375</miny>' \
              '<maxy>1808.070556640625</maxy>' \
              '</projectionBox>'
        element = ET.fromstring(xml)
        expected = {"projectionBox": {"minx": -2959.1533203125,
                                      "maxx": 2932.8466796875,
                                      "miny": -1827.929443359375,
                                      "maxy": 1808.070556640625}}
        actual = self.types.handle_projectionBox(element)
        assert_dict_equal(expected, actual)

    def test_axis_ref(self):
        xml = '<axisRef name="time1"/>'
        element = ET.fromstring(xml)

        expected = "time1"
        actual = self.types.handle_axisRef(element)
        assert_equal(expected, actual)

    def test_coord_trans_ref(self):
        xml = '<coordTransRef name="LambertConformal_Projection"/>'
        element = ET.fromstring(xml)

        expected = {"coordTransRef": "LambertConformal_Projection"}
        actual = self.types.handle_coordTransRef(element)
        assert_equal(expected, actual)

    def test_grid(self):
        xml = '<grid name="Temperature_isobaric" ' \
              'desc="Temperature @ Isobaric surface" ' \
              'shape="time1 isobaric3 y x" type="float">' \
              '<attribute name="units" value="K"/>' \
              '<attribute name="missing_value" type="float" value="-999.9"/>' \
              '<attribute name="Grib2_Parameter" type="int" value="0 0 0"/>' \
              '</grid>'
        element = ET.fromstring(xml)
        expected = {"name": "Temperature_isobaric",
                    "desc": "Temperature @ Isobaric surface",
                    "shape": "time1 isobaric3 y x",
                    "attributes": {"units": "K",
                                   "missing_value": [-999.9],
                                   "Grib2_Parameter": [0, 0, 0]}}
        actual = self.types.handle_grid(element)
        assert_dict_equal(expected["attributes"], actual["attributes"])
        assert_dict_equal(expected.pop("attributes", None),
                          actual.pop("attributes", None))

    def test_parameter(self):
        xml = '<parameter name="earth_radius" value="6371229.0 "/>'
        element = ET.fromstring(xml)
        expected = {"earth_radius": "6371229.0"}
        actual = self.types.handle_parameter(element)
        assert_dict_equal(expected, actual)

    def test_feature_type(self):
        xml = '<featureDataset type="station" ' \
              'url="/thredds/ncss/nws/metar/ncdecoded/' \
              'Metar_Station_Data_fc.cdmr"/>'
        element = ET.fromstring(xml)
        expected = {"type": "station",
                    "url": "/thredds/ncss/nws/metar/ncdecoded/"
                           "Metar_Station_Data_fc.cdmr"}
        actual = self.types.handle_featureDataset(element)
        assert_dict_equal(expected, actual)

    def test_variable(self):
        xml = '<variable name="precipitation_amount_hourly" type="float">' \
              '<attribute name="long_name" ' \
              'value="Hourly precipitation amount"/>' \
              '<attribute name="standard_name" ' \
              'value="precipitation_amount"/>' \
              '<attribute name="_FillValue" type="float" value="-99999.0"/>' \
              '<attribute name="units" value=".01 inches"/>' \
              '</variable>'
        element = ET.fromstring(xml)
        expected = {"name": "precipitation_amount_hourly",
                    "type": "float",
                    "attributes": {"long_name": "Hourly precipitation amount",
                                   "standard_name": "precipitation_amount",
                                   "_FillValue": [-99999.0],
                                   "units": ".01 inches"}}
        actual = self.types.handle_variable(element)
        assert_dict_equal(expected, actual)


class TestDatasetElements(object):

    def test_axis(self):
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
        actual = NcssDataset(element).axes
        assert actual
        assert_equal(len(actual), 1)
        assert actual["height_above_ground"]
        assert_equal(len(actual["height_above_ground"]), 4)
        assert actual["height_above_ground"]["attributes"]
        assert_equal(len(actual["height_above_ground"]["attributes"]), 8)

    def test_grid_set(self):
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
        actual = NcssDataset(element).gridsets
        assert actual
        assert_equal(len(actual), 1)
        assert actual["time1 isobaric3 y x"]
        gs = actual["time1 isobaric3 y x"]
        assert gs["axisRef"]
        assert_equal(len(gs["axisRef"]), 4)
        assert gs["coordTransRef"]
        assert gs["projectionBox"]
        assert_equal(len(gs["projectionBox"]), 4)
        assert gs["grid"]
        assert_equal(len(gs["grid"]), 2)
        for grid in gs["grid"]:
            assert_equal(len(gs["grid"][grid]), 4)
            assert gs["grid"][grid]["desc"]
            assert gs["grid"][grid]["shape"]
            assert gs["grid"][grid]["type"]
            assert_equal(gs["grid"][grid]["type"], "float")
            assert_equal(len(gs["grid"][grid]["attributes"]), 13)

    def test_coord_transform_valid(self):
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
        actual = NcssDataset(element).coordinate_transforms
        assert actual
        assert actual["LambertConformal_Projection"]
        assert_equal(len(actual["LambertConformal_Projection"]), 2)
        assert_equal(actual["LambertConformal_Projection"]["transformType"],
                     "Projection")
        parameters = actual["LambertConformal_Projection"]["parameters"]
        assert_equal(len(parameters), 5)
        expected = {"grid_mapping_name": "lambert_conformal_conic",
                    "latitude_of_projection_origin": "40.0",
                    "longitude_of_central_meridian": "262.0",
                    "standard_parallel": "40.0",
                    "earth_radius": "6371229.0"}
        assert_dict_equal(parameters, expected)

    def test_lat_lon_box(self):
        xml = '<LatLonBox>' \
              '<west>-140.1465</west>' \
              '<east>-56.1753</east>' \
              '<south>19.8791</south>' \
              '<north>49.9041</north>' \
              '</LatLonBox>'
        element = ET.fromstring(xml)
        expected = {"west": -140.1465,
                    "east": -56.1753,
                    "south": 19.8791,
                    "north": 49.9041}
        actual = NcssDataset(element).lat_lon_box
        assert actual
        assert_dict_equal(expected, actual)

    def test_time_span(self):
        xml = '<TimeSpan><begin>2015-06-19T12:00:00Z</begin>' \
              '<end>2015-06-23T18:00:00Z</end></TimeSpan>'
        element = ET.fromstring(xml)
        expected = {"begin": "2015-06-19T12:00:00Z",
                    "end": "2015-06-23T18:00:00Z"}
        actual = NcssDataset(element).time_span
        assert actual
        assert_dict_equal(expected, actual)

    def test_accept_list(self):
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
        expected = {"GridAsPoint": ["xml", "xml_file",
                                    "csv", "csv_file",
                                    "netcdf", "netcdf4"],
                    "Grid": ["netcdf", "netcdf4"]}
        actual = NcssDataset(element).accept_list
        assert_dict_equal(expected, actual)

    def test_station_accept_list(self):
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
        expected = {"PointFeatureCollection": ["xml", "text/xml",
                                               "csv", "text/csv",
                                               "netcdf", "netcdf4",
                                               "waterml2"]}
        actual = NcssDataset(element).accept_list

        assert_equal(len(actual.keys()), len(expected.keys()))
        for accept_type in actual:
            assert accept_type in expected

        for accept_type in expected:
            assert accept_type in actual

        assert_equal(sorted(expected["PointFeatureCollection"]),
                     sorted(actual["PointFeatureCollection"]))

    @recorder.use_cassette('Surface_Synoptic_Station_Dataset_xml')
    def test_full_ncss_station(self):
        url = ('http://thredds.ucar.edu/thredds/ncss/nws/synoptic/'
               'ncdecoded/Surface_Synoptic_Point_Data_fc.cdmr/dataset.xml')
        element = ET.fromstring(urlopen(url).read())
        parsed = NcssDataset(element)
        assert parsed

    @recorder.use_cassette('GFS_Global_0p5_Grid_Dataset_xml')
    def test_full_ncss_grid(self):
        url = ('http://thredds.ucar.edu/thredds/ncss/grib/NCEP/GFS/'
               'Global_0p5deg/GFS_Global_0p5deg_20150602_0000.grib2/'
               'dataset.xml')
        element = ET.fromstring(urlopen(url).read())
        parsed = NcssDataset(element)
        assert parsed
