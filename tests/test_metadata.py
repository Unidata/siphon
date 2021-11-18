# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Test parsing of metadata from a TDS client catalog."""

import logging
import xml.etree.ElementTree as ET  # noqa:N814

from siphon.metadata import _ComplexTypes, _SimpleTypes, TDSCatalogMetadata

log = logging.getLogger('siphon.metadata')
log.setLevel(logging.WARNING)

#
# tested:
#
# threddsMetadataGroup:
# =====================
#
# element_name="documentation" type="documentationType"
# element_name="serviceName"   type="xsd:string"
# element_name="authority"     type="xsd:string"
#
# simple types:
# =============
# name="upOrDown"
# name="dataFormatTypes"
# name="dataTypes"
#
# complex types:
# ==============
# name="spatialRange">
# type="controlledVocabulary"
# name="dateTypeFormatted"#
# name="sourceType"
# name="timeCoverageType">
#
# ref'd elements
# ==============
#
# element_name="metadata"
# element_name="geospatialCoverage"
# element_name="property":
# element_name="contributor"
# element_name="variable"
# element_name="variables"
# element_name="variableMap"
# element_name="dataSize"
# element_name="publisher"
# element_name="creator"
# element_name="keyword"
# element_name="project"
# element_name="dataFormat"
# element_name="date"
# element_name="dataType"
# element_name="date"
# element_name="timeCoverage"


class TestSimpleTypes:
    """Test parsing of simple types from metadata."""

    @classmethod
    def setup_class(cls):
        """Set up testing."""
        cls.st = _SimpleTypes()

    def test_up_or_down_valid(self):
        """Test parsing of zpositive attribute."""
        xml = '<geospatialCoverage zpositive="down" />'
        expected = {'zpositive': 'down'}
        element = ET.fromstring(xml)
        assert element.attrib
        val = self.st.handle_upOrDown(element)
        assert val == expected

    def test_data_format_type(self):
        """Test parsing of dataFormat tag."""
        xml = '<dataFormat>NcML</dataFormat>'
        expected = {'dataFormat': 'NcML'}
        element = ET.fromstring(xml)
        assert not element.attrib
        assert element.text
        val = self.st.handle_dataFormat(element)
        assert expected == val

    def test_data_type(self):
        """Test parsing of dataType tag."""
        xml = '<dataType>GRID</dataType>'
        expected = {'dataType': 'GRID'}
        element = ET.fromstring(xml)

        assert not element.attrib
        assert element.text
        val = self.st.handle_dataType(element)
        assert expected == val


class TestComplexTypes:
    """Test parsing of complex types from metadata."""

    @classmethod
    def setup_class(cls):
        """Set up testing."""
        cls.st = _ComplexTypes()

    def test_spatial_range_valid(self):
        """Test parsing of valid spatial range."""
        xml = '<northsouth><start>44.1</start>' \
              '<size>20.6</size><units>degrees_north</units>' \
              '</northsouth>'
        expected = {'start': 44.1,
                    'size': 20.6,
                    'units': 'degrees_north'}
        element = ET.fromstring(xml)
        actual = self.st.handle_spatialRange(element)

        assert actual == expected

    def test_controlled_vocabulary(self):
        """Test parsing of vocabulary tag."""
        xml = '<name vocabulary="MyVocabName">' \
              'NOAA and NCEP</name>'
        expected = {'vocabulary': 'MyVocabName',
                    'name': 'NOAA and NCEP'}
        element = ET.fromstring(xml)
        actual = self.st.handle_controlledVocabulary(element)
        assert expected == actual

    def test_date_type_formatted(self):
        """Test parsing of date types."""
        xml = '<start format="yyyy DDD" type="created">1999 189</start>'
        expected = {'format': 'yyyy DDD',
                    'type': 'created',
                    'value': '1999 189'}
        element = ET.fromstring(xml)
        actual = self.st.handle_dateTypeFormatted(element)
        assert expected == actual

    def test_source_type(self):
        """Test parsing of source."""
        xml = '<publisher><name vocabulary="DIF">UCAR/NCAR/CDP</name>' \
              '<contact url="http://dataportal.ucar.edu" ' \
              'email="cdp@ucar.edu"/></publisher>'

        element = ET.fromstring(xml)
        expected = {'vocabulary': 'DIF',
                    'name': 'UCAR/NCAR/CDP',
                    'email': 'cdp@ucar.edu',
                    'url': 'http://dataportal.ucar.edu'}
        actual = self.st.handle_sourceType(element)
        assert expected == actual

    def test_time_coverage_type1(self):
        """Test parsing of one form of timeCoverage tag."""
        xml = '<timeCoverage><end>present</end><duration>10 days</duration>' \
            '<resolution>15 minutes</resolution></timeCoverage>'
        element = ET.fromstring(xml)
        expected = {'end': 'present',
                    'duration': '10 days',
                    'resolution': '15 minutes'}
        actual = self.st.handle_timeCoverageType(element)
        assert expected == actual

    def test_time_coverage_type2(self):
        """Test parsing of a second form of timeCoverage tag."""
        xml = '<timeCoverage><start>1999-11-16T12:00:00</start>' \
            '<end>present</end></timeCoverage>'
        element = ET.fromstring(xml)
        expected = {'end': 'present',
                    'start': '1999-11-16T12:00:00'}
        actual = self.st.handle_timeCoverageType(element)
        assert expected == actual

    def test_time_coverage_type3(self):
        """Test parsing of a third type of timeCoverage tag."""
        xml = '<timeCoverage><start>1999-11-16T12:00:00</start>' \
            '<duration>P3M</duration></timeCoverage>'
        element = ET.fromstring(xml)
        expected = {'duration': 'P3M',
                    'start': '1999-11-16T12:00:00'}
        actual = self.st.handle_timeCoverageType(element)
        assert expected == actual

    def test_variable(self):
        """Test parsing of variable tags."""
        xml = '<variable name="wdir" vocabulary_name="Wind Direction" ' \
              'units= "degrees">Wind Direction @ surface</variable>'
        element = ET.fromstring(xml)
        expected = {'name': 'wdir',
                    'vocabulary_name': 'Wind Direction',
                    'units': 'degrees',
                    'description': 'Wind Direction @ surface'}
        actual = self.st.handle_variable(element)
        assert expected == actual

    def test_variable2(self):
        """Test parsing another variable tag."""
        xml = '<variable name="wdir"></variable>'
        element = ET.fromstring(xml)
        expected = {'name': 'wdir'}
        actual = self.st.handle_variable(element)
        assert expected == actual

    def test_variable3(self):
        """Test parsing a third variable tag."""
        xml = '<variable name="wdir">Wind Direction @ surface</variable>'
        element = ET.fromstring(xml)
        expected = {'name': 'wdir',
                    'description': 'Wind Direction @ surface'}
        actual = self.st.handle_variable(element)
        assert expected == actual

    def test_variable_map(self):
        """Test parsing a variableMap tag."""
        xml = '<variableMap xmlns:xlink="http://www.w3.org/1999/xlink" ' \
              'xlink:href="../standardQ/Eta.xml" />'
        element = ET.fromstring(xml)
        expected = {
            '{http://www.w3.org/1999/xlink}href': '../standardQ/Eta.xml'}
        actual = self.st.handle_variableMap(element)
        assert expected == actual

    def test_variable_map2(self):
        """Test parsing another form of VariableMap tag."""
        xml = '<variableMap xmlns:xlink="http://www.w3.org/1999/xlink" ' \
              'xlink:href="../standardQ/Eta.xml" xlink:title="variables"/>'
        element = ET.fromstring(xml)
        expected = {'{http://www.w3.org/1999/xlink}href':
                    '../standardQ/Eta.xml',
                    '{http://www.w3.org/1999/xlink}title':
                        'variables'}
        actual = self.st.handle_variableMap(element)
        assert expected == actual

    def test_variables(self):
        """Test parsing multiple variables."""
        xml = '<variables vocabulary="CF-1.0">' \
              '<variable name="wv" vocabulary_name="Wind Speed" ' \
              'units="m/s">Wind Speed @ surface</variable>' \
              '<variable name="wdir" vocabulary_name="Wind Direction" ' \
              'units= "degrees">Wind Direction @ surface</variable>' \
              '<variable name="o3c" vocabulary_name="Ozone Concentration"' \
              ' units="g/g">Ozone Concentration @ surface</variable>' \
              '</variables>'
        element = ET.fromstring(xml)
        actual = self.st.handle_variables(element)
        assert 'vocabulary' in actual
        assert actual['vocabulary'] == 'CF-1.0'
        assert 'variables' in actual
        assert len(actual['variables']) == 3
        assert 'variableMaps' not in actual

    def test_variables2(self):
        """Test parsing multiple variables from a variableMap."""
        xml = '<variables vocabulary="GRIB-NCEP" ' \
              ' xmlns:xlink="http://www.w3.org/1999/xlink" ' \
              'xlink:href="http://www.unidata.ucar.edu/GRIB-NCEPtable2.xml">' \
              '<variableMap xlink:href="../standardQ/Eta.xml" />' \
              '</variables>'
        element = ET.fromstring(xml)
        actual = self.st.handle_variables(element)
        assert 'vocabulary' in actual
        assert actual['vocabulary'] == 'GRIB-NCEP'
        assert 'variables' not in actual
        assert 'variableMaps' in actual
        assert len(actual['variableMaps']) == 1

    def test_data_size(self):
        """Test parsing dataSize tag."""
        xml = '<dataSize units="Kbytes">123</dataSize>'
        element = ET.fromstring(xml)
        actual = self.st.handle_dataSize(element)
        assert 'units' in actual
        assert actual['units'] == 'Kbytes'
        assert actual['size'] == 123


class TestProperty:
    """Test parsing of property tags."""

    @classmethod
    def setup_class(cls):
        """Set up testing."""
        xml = '<property name="Conventions" value="CF-1.6" />'
        element = ET.fromstring(xml)
        cls.md = TDSCatalogMetadata(element).metadata
        cls.element_name = 'property'

    def test_prop(self):
        """Test finding the property tag in the metadata."""
        assert self.element_name in self.md

    def test_prop_not_empty(self):
        """Test that the property tag is not empty."""
        for entry in self.md[self.element_name]:
            assert entry


class TestContributor:
    """Test parsing Contributor tags."""

    @classmethod
    def setup_class(cls):
        """Set up testing with common metadata tag."""
        xml = '<contributor role="PI">Jane Doe</contributor>'
        element = ET.fromstring(xml)
        cls.md = TDSCatalogMetadata(element).metadata
        cls.element_name = 'contributor'

    def test_contributor(self):
        """Test finding the Contributor tag in the metadata."""
        assert self.element_name in self.md

    def test_contributor_for_role_not_empty(self):
        """Test non-empty contributor role."""
        for entry in self.md[self.element_name]:
            assert entry


class TestGeospatialCoverage:
    """Test parsing GeospatialCoverage tags."""

    @classmethod
    def setup_class(cls):
        """Set up tests with a common set of xml."""
        cls.element_name = 'geospatialCoverage'

        xml1 = '<geospatialCoverage zpositive="down">' \
               '<northsouth>' \
               '<start>10</start><size>80</size>' \
               '<resolution>2</resolution>' \
               '<units>degrees_north</units>' \
               '</northsouth>' \
               '<eastwest>' \
               '<start>-130</start>' \
               '<size>260</size>' \
               '<resolution>2</resolution>' \
               '<units>degrees_east</units>' \
               '</eastwest>' \
               '<updown>' \
               '<start>0</start>' \
               '<size>22</size>' \
               '<resolution>0.5</resolution>' \
               '<units>km</units>' \
               '</updown>' \
               '</geospatialCoverage>'

        xml2 = '<geospatialCoverage>' \
               '<name vocabulary="Thredds">global</name>' \
               '</geospatialCoverage>'

        cls.xml_warn1 = '<geospatialCoverage crazy="yep">' \
            '</geospatialCoverage>'

        cls.xml_warn2 = '<geospatialCoverage zpositive="waka-waka">' \
            '</geospatialCoverage>'

        cls.md1 = TDSCatalogMetadata(ET.fromstring(xml1)).metadata
        cls.md2 = TDSCatalogMetadata(ET.fromstring(xml2)).metadata

    def test_geospatial_coverage_attr1(self):
        """Test parsing of geospatialCoverage."""
        assert self.element_name in self.md1
        for entry in self.md1[self.element_name]:
            assert entry

    def test_geospatial_coverage_attr2(self):
        """Test parsing geospatialCoverage with zpositive."""
        # can we detect this:
        # <geospatialCoverage zpositive="down">
        for entry in self.md1[self.element_name]:
            if 'zpositive' in entry:
                assert entry['zpositive']['zpositive'] in {'up', 'down'}


class TestMetadata:
    """Test parsing other metadata tags."""

    @staticmethod
    def _make_element(xml_str):
        return ET.fromstring(xml_str)

    def test_documentation_element_no_type(self):
        """Test parsing generic documentation."""
        xml = '<documentation>Used in doubled CO2 scenario</documentation>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'documentation' in md
        assert 'generic' in md['documentation']
        assert len(md['documentation']['generic']) > 0
        for entry in md['documentation']['generic']:
            assert entry != []

    def test_documentation_element_summary(self):
        """Test parsing a summary element."""
        xml = '<documentation type="summary"> The SAGE III Ozone Loss and ' \
              'Validation Experiment (SOLVE) was a measurement campaign ' \
              'designed to examine the processes controlling ozone levels ' \
              'at mid- to high high latitudes. Measurements were made in ' \
              'the Arctic high-latitude region in winter using the NASA ' \
              'DC-8 and ER-2 aircraft,as well as balloon platforms and ' \
              'ground-based instruments. </documentation>'

        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'documentation' in md
        assert 'summary' in md['documentation']
        assert len(md['documentation']['summary']) > 0
        for entry in md['documentation']['summary']:
            assert entry != []

    def test_documentation_element_rights(self):
        """Test parsing rights documentation."""
        xml = '<documentation type="rights"> Users of these data files are ' \
              'expected  to follow the NASA ESPO Archive guidelines for ' \
              'use of the SOLVE data, including consulting with the PIs ' \
              'of the individual measurements  for interpretation and ' \
              'credit.</documentation>'

        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'documentation' in md
        assert 'rights' in md['documentation']
        assert len(md['documentation']['rights']) > 0
        for entry in md['documentation']['rights']:
            assert entry != []

    def test_documentation_element_processing_level(self):
        """Test parsing processing_level documentation."""
        xml = '<documentation type="processing_level"> Transmitted through ' \
              'Unidata Internet Data Distribution.</documentation>'

        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'documentation' in md
        assert 'processing_level' in md['documentation']
        assert len(md['documentation']['processing_level']) > 0
        for entry in md['documentation']['processing_level']:
            assert entry != []

    def test_documentation_element_reference_time(self):
        """Test parsing reference time documentation."""
        xml = '<documentation type="Reference Time">' \
              '2015-05-28T12:00:00Z</documentation>'

        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'documentation' in md
        assert 'Reference Time' in md['documentation']
        assert len(md['documentation']['Reference Time']) > 0
        for entry in md['documentation']['Reference Time']:
            assert entry != []

    def test_documentation_element_xlink(self):
        """Test parsing xlink documentation."""
        xml = '<documentation xmlns:xlink="http://www.w3.org/1999/xlink" ' \
              'xlink:href="http://espoarchive.nasa.gov/archive/index.html" ' \
              'xlink:title="Earth Science Project Office Archives"/>'

        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'documentation' in md
        assert 'xlink' in md['documentation']
        assert len(md['documentation']['xlink']) > 0
        for entry in md['documentation']['xlink']:
            assert entry['title']
            assert entry['href']

    def test_service_type(self):
        """Test parsing service type tags."""
        xml = '<serviceName>VirtualServices</serviceName>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'serviceName' in md
        assert md['serviceName'] == 'VirtualServices'

    def test_authority(self):
        """Test parsing authority tags."""
        xml = '<authority>edu.ucar.unidata</authority>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'authority' in md
        assert len(md['authority']) == 1
        assert md['authority'][0] == 'edu.ucar.unidata'

    def test_publisher(self):
        """Test parsing publisher tags."""
        xml = '<publisher><name vocabulary="DIF">UCAR/UNIDATA</name>' \
              '<contact url="http://www.unidata.ucar.edu/" ' \
              'email="support@unidata.ucar.edu"/>' \
              '</publisher>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'publisher' in md
        assert len(md['publisher']) == 1
        assert md['publisher'][0]['vocabulary'] == 'DIF'
        assert md['publisher'][0]['name'] == 'UCAR/UNIDATA'
        assert md['publisher'][0]['url'] == 'http://www.unidata.ucar.edu/'
        assert md['publisher'][0]['email'] == 'support@unidata.ucar.edu'

    def test_creator(self):
        """Test parsing creator tags."""
        xml = '<creator><name vocabulary="DIF">DOC/NOAA/NWS/NCEP</name>' \
              '<contact url="http://www.ncep.noaa.gov/" ' \
              'email="http://www.ncep.noaa.gov/mail_liaison.shtml"/>' \
              '</creator>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'creator' in md
        assert len(md['creator']) == 1
        assert md['creator'][0]['vocabulary'] == 'DIF'
        assert md['creator'][0]['name'] == 'DOC/NOAA/NWS/NCEP'
        assert md['creator'][0]['url'] == 'http://www.ncep.noaa.gov/'
        assert md['creator'][0]['email'] == 'http://www.ncep.noaa.gov/mail_liaison.shtml'

    def test_keyword(self):
        """Test parsing keyword tags."""
        xml = '<keyword>Ocean Biomass</keyword>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'keyword' in md
        assert len(md['keyword']) == 1
        assert md['keyword'][0]['name'] == 'Ocean Biomass'

    def test_project(self):
        """Test parsing project tags."""
        xml = '<project vocabulary="DIF">NASA Earth Science Project Office, ' \
              'Ames Research Center</project>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'project' in md
        assert len(md['project']) == 1
        assert md['project'][0]['vocabulary'] == 'DIF'
        assert md['project'][0]['name'] == 'NASA Earth Science Project Office, ' \
                                           'Ames Research Center'

    def test_data_format(self):
        """Test parsing dataFormat tags."""
        xml = '<dataFormat>GRIB-1</dataFormat>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'dataFormat' in md
        assert md['dataFormat'] == 'GRIB-1'

    def test_data_malformed_format(self, caplog):
        """Test getting a warning for a malformed dataFormat tag."""
        xml = '<dataFormat>netCDF-4</dataFormat>'
        element = self._make_element(xml)
        TDSCatalogMetadata(element)
        assert 'Value netCDF-4 not valid for type dataFormat' in caplog.text

    def test_data_type(self):
        """Test parsing dataType tags."""
        xml = '<dataType>GRID</dataType>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'dataType' in md
        assert md['dataType'] == 'GRID'

    def test_date(self):
        """Test parsing a date tag."""
        xml = '<date type="modified">2015-06-11T02:09:52Z</date>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'date' in md
        assert len(md['date']) == 1
        assert md['date'][0]['type'] == 'modified'
        assert md['date'][0]['value'] == '2015-06-11T02:09:52Z'

    def test_time_coverage(self):
        """Test parsing a timeCoverage tag."""
        xml = '<timeCoverage><end>present</end><duration>45 days</duration>' \
              '</timeCoverage>'
        element = self._make_element(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'timeCoverage' in md
        assert len(md['timeCoverage']) == 1
        assert md['timeCoverage'][0]['end'] == 'present'
        assert md['timeCoverage'][0]['duration'] == '45 days'

    def test_external_metadata(self):
        """Test an embedded metadata element that points to an external document."""
        xml = '<metadata inherited="true">' \
              '<serviceName>ALL</serviceName>' \
              '<metadata xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href=' \
              '"http://gis.ncdc.noaa.gov/geoportal/rest/document?' \
              'id={6439CC43-0208-4AD6-BF6F-48F586F7541D}" ' \
              'xlink:title="ISO 19115-2:2009(E) - Collection Level Metadata"/>' \
              '</metadata>'
        element = ET.fromstring(xml)
        md = TDSCatalogMetadata(element).metadata
        # make sure other metadata is still captured
        assert 'serviceName' in md
        # make sure the embedded metadata element gets processed and added
        expected_title = 'ISO 19115-2:2009(E) - Collection Level Metadata'
        expected_href = 'http://gis.ncdc.noaa.gov/geoportal/rest/document?' \
                        'id={6439CC43-0208-4AD6-BF6F-48F586F7541D}'
        assert 'external_metadata' in md
        assert expected_title in md['external_metadata']
        assert md['external_metadata'][expected_title] == expected_href

    def test_external_metadata_non_xlink(self, caplog):
        """Test an non-xlink embedded external metadata element."""
        xml = '<metadata inherited="true">' \
              '<serviceName>ALL</serviceName>' \
              '<metadata url="http://gis.ncdc.noaa.gov/geoportal/rest/document?' \
              'id={6439CC43-0208-4AD6-BF6F-48F586F7541D}" ' \
              'name="ISO 19115-2:2009(E) - Collection Level Metadata"/>' \
              '</metadata>'
        element = ET.fromstring(xml)
        md = TDSCatalogMetadata(element).metadata
        assert 'serviceName' in md
        assert 'external_metadata' not in md
        assert 'Cannot parse embedded metadata element' in caplog.text
