# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Helps support reading and parsing metadata elements from a TDS client catalog."""

from __future__ import print_function

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.ERROR)
log.addHandler(logging.StreamHandler())


class _SimpleTypes(object):
    def __init__(self):
        self._valid = {'dataFormat': self._load_valid_data_format_types(),
                       'upOrDown': self._load_valid_up_or_down(),
                       'dataType': self._load_valid_data_types()}

    @staticmethod
    def _load_valid_data_types():
        valid = ['grid',
                 'image',
                 'point',
                 'radial',
                 'station',
                 'swath',
                 'trajectory']
        return valid

    @staticmethod
    def _load_valid_data_format_types():
        import mimetypes
        valid = ['BUFR',
                 'ESML',
                 'GEMPAK',
                 'GINI',
                 'GRIB-1',
                 'GRIB-2',
                 'HDF4',
                 'HDF5',
                 'McIDAS-AREA',
                 'NcML',
                 'NetCDF',
                 'NetCDF-4',
                 'NEXRAD2',
                 'NIDS',
                 'image/gif',
                 'image/jpeg',
                 'image/tiff',
                 'text/csv',
                 'text/html',
                 'text/plain',
                 'text/tab-separated-values',
                 'text/xml',
                 'video/mpeg',
                 'video/quicktime',
                 'video/realtime']

        valid_mime_types = list(mimetypes.types_map.values())
        valid.extend(valid_mime_types)
        return valid

    @staticmethod
    def _load_valid_up_or_down():
        return ['up', 'down']

    def handle_upOrDown(self, element):  # noqa
        # name="upOrDown"
        #   <xsd:restriction base="xsd:token">
        #    <xsd:enumeration value="up"/>
        #    <xsd:enumeration value="down"/>
        #   </xsd:restriction>
        #
        type_name = 'upOrDown'
        valid = self._valid[type_name]
        for attrib in element.attrib:
            attr = attrib
            val = element.attrib[attr]
            if val not in valid:
                log.warning('Value %s not valid for type %s: must be %s',
                            val, type_name, valid)
        return {attr: val}

    def handle_dataFormat(self, element):  # noqa
        # name="dataFormatTypes"
        #   <xsd:union memberTypes="xsd:token mimeType">
        #     <xsd:simpleType>
        #       <xsd:restriction base="xsd:token">
        #         <xsd:enumeration value="BUFR"/>
        #         <xsd:enumeration value="ESML"/>
        #         <xsd:enumeration value="GEMPAK"/>
        #         <xsd:enumeration value="GINI"/>
        #         <xsd:enumeration value="GRIB-1"/>
        #         <xsd:enumeration value="GRIB-2"/>
        #         <xsd:enumeration value="HDF4"/>
        #         <xsd:enumeration value="HDF5"/>
        #         <xsd:enumeration value="McIDAS-AREA"/>
        #         <xsd:enumeration value="NcML"/>
        # 		  <xsd:enumeration value="NetCDF"/>
        # 		  <xsd:enumeration value="NetCDF-4"/>
        #         <xsd:enumeration value="NEXRAD2"/>
        #         <xsd:enumeration value="NIDS"/>
        #
        #         <xsd:enumeration value="image/gif"/>
        #         <xsd:enumeration value="image/jpeg"/>
        #         <xsd:enumeration value="image/tiff"/>
        #         <xsd:enumeration value="text/csv"/>
        #         <xsd:enumeration value="text/html"/>
        # 		  <xsd:enumeration value="text/plain"/>
        # 		  <xsd:enumeration value="text/tab-separated-values"/>
        #         <xsd:enumeration value="text/xml"/>
        #         <xsd:enumeration value="video/mpeg"/>
        #         <xsd:enumeration value="video/quicktime"/>
        #         <xsd:enumeration value="video/realtime"/>
        #       </xsd:restriction>
        #     </xsd:simpleType>
        #   </xsd:union>
        #
        # name="mimeType"
        #   <xsd:restriction base="xsd:token">
        #     <xsd:annotation>
        #       <xsd:documentation>any valid mime type
        #         (see http://www.iana.org/assignments/media-types/)
        #       </xsd:documentation>
        #     </xsd:annotation>
        #   </xsd:restriction>
        #   NOTE: to see if mimetype is valude, check against
        #         mimetypes.types_map.values
        #
        type_name = 'dataFormat'
        valid = self._valid[type_name]
        val = element.text
        if val not in valid:
            log.warning('Value %s not valid for type %s: must be %s',
                        val, type_name, valid)
        return {type_name: val}

    def handle_dataType(self, element):  # noqa
        # name="dataTypes"
        #   <xsd:union memberTypes="xsd:token">
        #     <xsd:simpleType>
        #       <xsd:restriction base="xsd:token">
        #         <xsd:enumeration value="Grid"/>
        #         <xsd:enumeration value="Image"/>
        #         <xsd:enumeration value="Point"/>
        #         <xsd:enumeration value="Radial"/>
        #         <xsd:enumeration value="Station"/>
        #         <xsd:enumeration value="Swath"/>
        #         <xsd:enumeration value="Trajectory"/>
        #       </xsd:restriction>
        #     </xsd:simpleType>
        #   </xsd:union>
        type_name = 'dataType'
        valid = self._valid[type_name]
        # case insensitive

        val = element.text
        if val.lower() not in valid:
            log.warning('Value %s not valid for type %s: must be %s',
                        val, type_name, valid)
        return {type_name: val}


class _ComplexTypes(object):
    @staticmethod
    def _get_tag_name(element):
        if '}' in element.tag:
            element_name = element.tag.split('}')[-1]
        else:
            element_name = element.tag
        return element_name

    @staticmethod
    def _spatial_range_req_children():
        return ['start', 'size']

    @staticmethod
    def _spatial_range_opt_children():
        return ['resolution', 'units']

    @staticmethod
    def _date_type_formatted_valid_attrs():
        return ['format', 'type']

    @staticmethod
    def _controlled_vocatulary_opt_attrs():
        return ['vocabulary']

    @staticmethod
    def _variable_opt_attrs():
        return ['vocabulary_name', 'units']

    @staticmethod
    def _variable_req_attrs():
        return ['name']

    @staticmethod
    def _variables_opt_attrs():
        return ['vocabulary']

    @staticmethod
    def _data_size_req_attrs():
        return ['units']

    #
    # complex types:
    # ==============
    def handle_spatialRange(self, element):  # noqa
        # name="spatialRange">
        #   <xsd:sequence>
        #    <xsd:element name="start" type="xsd:double"  />
        #    <xsd:element name="size" type="xsd:double" />
        #    <xsd:element name="resolution" type="xsd:double" minOccurs="0" />
        #    <xsd:element name="units" type="xsd:string" minOccurs="0" />
        #   </xsd:sequence>
        type_name = 'spatialRange'
        req_children = self._spatial_range_req_children()
        opt_children = self._spatial_range_opt_children()
        valid = req_children + opt_children

        spatial_range = {}
        for child in element:
            child_name = child.tag
            if child_name in valid:
                if child_name != 'units':
                    spatial_range[child.tag] = float(child.text)
                else:
                    spatial_range[child.tag] = child.text
            else:
                # child not valid
                log.warning('%s is not valid for type %s',
                            child_name, type_name)
        return spatial_range

    def handle_controlledVocabulary(self, element):  # noqa
        #
        # type="controlledVocabulary"
        #   <xsd:simpleContent>
        #    <xsd:extension base="xsd:string">
        #     <xsd:attribute name="vocabulary" type="xsd:string" />
        #    </xsd:extension>
        #   </xsd:simpleContent>
        #
        type_name = 'controlledVocabulary'

        opt_attrs = self._controlled_vocatulary_opt_attrs()
        val = {}
        for attr in element.attrib:
            if attr not in opt_attrs:
                log.warning('%s not a valid attribute for %s', type_name,
                            attr)
            else:
                val[attr] = element.attrib[attr]

        name = element.text
        tmp = {'name': name}
        if val:
            tmp.update(val)
        return tmp

    def handle_dateTypeFormatted(self, element):  # noqa
        # name="dateTypeFormatted"
        #   <xsd:simpleContent>
        #     <xsd:extension base="dateType">
        #       <xsd:attribute name="format" type="xsd:string" /> // from
        #                                        java.text.SimpleDateFormat
        #       <xsd:attribute name="type" type="dateEnumTypes" />
        #     </xsd:extension>
        #
        type_name = 'dateTypeFormatted'
        valid_attrs = self._date_type_formatted_valid_attrs()
        val = {}
        for attr in element.attrib:
            if attr not in valid_attrs:
                log.warning('%s is not a valid attribute for %s', attr,
                            type_name)
            else:
                val[attr] = element.attrib[attr]

        val['value'] = element.text

        return val

    def handle_sourceType(self, element):  # noqa
        # name="sourceType"
        #   <xsd:sequence>
        #     <xsd:element name="name" type="controlledVocabulary"/>
        #     <xsd:element name="contact">
        #       <xsd:complexType>
        #         <xsd:attribute name="email" type="xsd:string"
        #                                     use="required"/>
        #         <xsd:attribute name="url" type="xsd:anyURI"/>
        #       </xsd:complexType>
        #     </xsd:element>
        #   </xsd:sequence>
        parsed = {}
        for child in element:
            value = {}
            if child.tag == 'name':
                value = self.handle_controlledVocabulary(child)
            elif child.tag == 'contact':
                if 'url' in child.attrib:
                    value['url'] = child.attrib['url']
                if 'email' in child.attrib:
                    value['email'] = child.attrib['email']
                else:
                    log.warning("'contact' must have an attribute: 'email'")
                    value['email'] = 'missing'
            if value:
                parsed.update(value)
        return parsed

    def handle_timeCoverageType(self, element):  # noqa
        # name="timeCoverageType">
        #   <xsd:sequence>
        #     <xsd:choice minOccurs="2" maxOccurs="3" >
        #       <xsd:element name="start" type="dateTypeFormatted"/>
        #       <xsd:element name="end" type="dateTypeFormatted"/>
        #       <xsd:element name="duration" type="duration"/>
        #     </xsd:choice>
        #     <xsd:element name="resolution" type="duration" minOccurs="0"/>
        #   </xsd:sequence>
        parsed = {}
        tags = []
        for child in element:
            tags.append(child.tag)
        valid_num_elements = len(tags) >= 2 & len(tags) <= 3
        if valid_num_elements:
            for child in element:
                value = {}
                if child.tag in ['start', 'end']:
                    processed = self.handle_dateTypeFormatted(child)
                    value[child.tag] = processed['value']
                elif child.tag in ['duration', 'resolution']:
                    value[child.tag] = child.text
                parsed.update(value)
        else:
            log.warning('Not enough elements to make a valid timeCoverage')

        return parsed

    def handle_variable(self, element):
        # element_name="variable"
        #   <xsd:complexType mixed="true">
        #     <xsd:attribute name="name" type="xsd:string" use="required"/>
        #     <xsd:attribute name="vocabulary_name" type="xsd:string"
        #                    use="optional"/>
        #     <xsd:attribute name="units" type="xsd:string"/>
        #   </xsd:complexType>
        type_name = 'variable'
        opt_attrs = self._variable_opt_attrs()
        req_attrs = self._variable_req_attrs()
        valid_attrs = opt_attrs + req_attrs
        valid = True
        variable = {}
        for req_attr in req_attrs:
            if req_attr not in element.attrib:
                valid = False
                log.warning('%s must have an attribute %s', type_name,
                            req_attr)
        if valid:
            if element.text:
                variable['description'] = element.text
            for attr in element.attrib:
                if attr in valid_attrs:
                    variable[attr] = element.attrib[attr]

        return variable

    @staticmethod
    def handle_variableMap(element):  # noqa
        # element_name="variableMap"
        #   <xsd:complexType>
        #     <xsd:attributeGroup ref="XLink"/>
        #   </xsd:complexType>
        type_name = 'variableMap'  # noqa
        var_map = {}
        for attr in element.attrib:
            var_map[attr] = element.attrib[attr]

        return var_map

    def handle_variables(self, element):
        # element_name="variables"
        #   <xsd:complexType>
        #     <xsd:choice>
        #       <xsd:element ref="variable" minOccurs="0"
        #                    maxOccurs="unbounded"/>
        #       <xsd:element ref="variableMap" minOccurs="0"/>
        #     </xsd:choice>
        #     <xsd:attribute name="vocabulary" type="variableNameVocabulary"
        #                    use="optional"/>
        #     <xsd:attributeGroup ref="XLink"/>
        #   </xsd:complexType>
        type_name = 'variables'  # noqa
        variables = {}
        variable_list = []
        variable_map_list = []
        for child in element:
            child_type = self._get_tag_name(child)

            if child_type == 'variable':
                var = self.handle_variable(child)
                variable_list.append(var)
            elif child_type == 'variableMap':
                var_map = self.handle_variableMap(element)
                variable_map_list.append(var_map)

        opt_attrs = self._variables_opt_attrs()
        for attr in element.attrib:
            if attr in opt_attrs:
                variables[attr] = element.attrib[attr]

        if variable_list:
            variables['variables'] = variable_list

        if variable_map_list:
            variables['variableMaps'] = variable_map_list
        return variables

    def handle_dataSize(self, element):  # noqa
        #   <xsd:complexType>
        #     <xsd:simpleContent>
        #     <xsd:extension base="xsd:string">
        #       <xsd:attribute name="units" type="xsd:string" use="required"/>
        #     </xsd:extension>
        #     </xsd:simpleContent>
        #   </xsd:complexType>
        #
        req_attrs = self._data_size_req_attrs()
        data_size = {'size': float(element.text)}

        for attr in element.attrib:
            if attr in req_attrs:
                data_size[attr] = element.attrib[attr]

        return data_size


class TDSCatalogMetadata(object):
    """Hold information contained in the catalog Metadata tag.

    Attributes
    ----------
    metadata : dict[str, object]
        The dictionary containing the metadata entries

    """

    def __init__(self, element, metadata_in=None):
        """Initialize a :class:`TDSCatalogMetadata` object.

        Parameters
        ----------
        element : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing a metadata node
        metadata_in : dict[str, object], optional
            Parent metadata to inherit, if appropriate. Defaults to None.

        """
        self._ct = _ComplexTypes()
        self._st = _SimpleTypes()
        self._sts = _SimpleTypes.__dict__
        self._cts = _ComplexTypes.__dict__

        inherited = False
        if 'inherited' in element.attrib:
            inherited = element.attrib['inherited']
            if inherited == 'true':
                inherited = True
            else:
                inherited = False

        if metadata_in and inherited:
            # only inherit metadata passed in if the new metadata
            # element has inherit set to True
            self.metadata = metadata_in
        else:
            self.metadata = {'inherited': inherited}

        element_name = self._get_tag_name(element)
        if element_name == 'metadata':
            for child in element:
                self._parse_element(child)
        else:
            self._parse_element(element)

    @staticmethod
    def _get_tag_name(element):
        if '}' in element.tag:
            element_name = element.tag.split('}')[-1]
        else:
            element_name = element.tag
        return element_name

    def _get_handler(self, handler_name):
        handler_name = 'handle_' + handler_name
        if handler_name in self._cts:
            return getattr(self._ct, handler_name)
        elif handler_name in self._sts:
            return getattr(self._st, handler_name)
        else:
            msg = 'cannot find handler for element {}'.format(handler_name)
            log.warning(msg)

    def _parse_element(self, element):

        element_name = self._get_tag_name(element)

        parser = {'documentation': self._parse_documentation,
                  'property': self._parse_property,
                  'contributor': self._parse_contributor,
                  'geospatialCoverage': self._parse_geospatial_coverage,
                  'serviceName': self._parse_service_name,
                  'authority': self._parse_authority,
                  'publisher': self._parse_publisher,
                  'creator': self._parse_creator,
                  'keyword': self._parse_keyword,
                  'project': self._parse_project,
                  'dataFormat': self._parse_data_format,
                  'dataType': self._parse_data_type,
                  'date': self._parse_date,
                  'timeCoverage': self._parse_timeCoverage,
                  'variableMap': self._parse_variableMap,
                  'variables': self._parse_variables}

        try:
            parser[element_name](element)
        except KeyError:
            log.warning('No parser found for element %s', element_name)

    def _parse_documentation(self, element):
        # <xsd:simpleType name="documentationEnumTypes">
        #  <xsd:union memberTypes="xsd:token">
        #   <xsd:simpleType>
        #    <xsd:restriction base="xsd:token">
        #     <xsd:enumeration value="funding"/>
        #     <xsd:enumeration value="history"/>
        #     <xsd:enumeration value="processing_level"/>
        #     <xsd:enumeration value="rights"/>
        #     <xsd:enumeration value="summary"/>
        #    </xsd:restriction>
        #   </xsd:simpleType>
        #  </xsd:union>
        # </xsd:simpleType>
        #
        # <xsd:complexType name="documentationType" mixed="true">
        #  <xsd:sequence>
        #   <xsd:any namespace="http://www.w3.org/1999/xhtml" minOccurs="0"
        #         maxOccurs="unbounded" processContents="strict"/>
        #  </xsd:sequence>
        #  <xsd:attribute name="type" type="documentationEnumTypes"/>
        #  <xsd:attributeGroup ref="XLink" />
        # </xsd:complexType>
        xlink_href_attr = '{http://www.w3.org/1999/xlink}href'
        xlink_title_attr = '{http://www.w3.org/1999/xlink}title'

        # doc_enum_types = ("funding", "history", "processing_level", "rights",
        #                  "summary")
        known = 'type' in element.attrib
        # document element has no attributes
        plain_doc = not element.attrib
        md = self.metadata
        md.setdefault('documentation', {})
        if known or plain_doc:
            if known:
                doc_type = element.attrib['type']
            else:
                doc_type = 'generic'
            md['documentation'].setdefault(doc_type, []).append(element.text)
        elif xlink_href_attr in element.attrib:
            title = element.attrib[xlink_title_attr]
            href = element.attrib[xlink_href_attr]
            xlink = {'title': title, 'href': href}
            md['documentation'].setdefault('xlink', []).append(xlink)
        self.metadata = md

    def _parse_property(self, element):
        # <xsd:element name="property">
        #  <xsd:complexType>
        #   <xsd:attribute name="name" type="xsd:string"/>
        #   <xsd:attribute name="value" type="xsd:string"/>
        #  </xsd:complexType>
        # </xsd:element>
        name = element.attrib['name']
        value = element.attrib['value']
        self.metadata.setdefault('property', {})[name] = value

    def _parse_contributor(self, element):
        # <xsd:element name="contributor">
        #   <xsd:complexType>
        #     <xsd:simpleContent>
        #       <xsd:extension base="xsd:string">
        #         <xsd:attribute name="role" type="xsd:string"
        #                        use="required"/>
        #       </xsd:extension>
        #     </xsd:simpleContent>
        #   </xsd:complexType>
        # </xsd:element>
        element_type = 'contributor'
        role = element.attrib['role']
        name = element.text
        self.metadata.setdefault(element_type, {}).setdefault(role, []).append(name)

    def _parse_geospatial_coverage(self, element):
        element_type = 'geospatialCoverage'
        md = {}
        # <xsd:element name="geospatialCoverage">
        #  <xsd:complexType>
        #   <xsd:sequence>
        #    <xsd:element name="northsouth" type="spatialRange"
        #                 minOccurs="0" />
        #    <xsd:element name="eastwest" type="spatialRange"
        #                 minOccurs="0" />
        #    <xsd:element name="updown" type="spatialRange"
        #                 minOccurs="0" />
        #    <xsd:element name="name" type="controlledVocabulary"
        #                 minOccurs="0" maxOccurs="unbounded"/>
        #   </xsd:sequence>
        #
        #   <xsd:attribute name="zpositive" type="upOrDown" default="up"/>
        #  </xsd:complexType>
        # </xsd:element>
        elements = {'northsouth': 'spatialRange',
                    'eastwest': 'spatialRange',
                    'updown': 'spatialRange',
                    'name': 'controlledVocabulary'
                    }
        attrs = {'zpositive': 'upOrDown'}

        if element.attrib:
            for attr in element.attrib:
                if attr in attrs:
                    handler_name = attrs[attr]
                    handler = self._get_handler(handler_name)
                    value = handler(element)
                    md.update({attr: value})
                else:
                    log.warning('Attr on %s : %s not captured', attr,
                                element_type)

        for child in element:
            child_name = child.tag
            if child_name in elements:
                handler_name = elements[child_name]
                handler = self._get_handler(handler_name)
                value = handler(child)
                md.update(value)
        self.metadata.setdefault(element_type, []).append(md)

    def _parse_service_name(self, element):
        # can only have one serviceName
        element_type = 'serviceName'
        self.metadata[element_type] = element.text

    def _parse_authority(self, element):
        element_type = 'authority'
        self.metadata.setdefault(element_type, []).append(element.text)

    def _parse_publisher(self, element):
        element_type = 'publisher'
        parsed = self._ct.handle_sourceType(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_creator(self, element):
        element_type = 'creator'
        parsed = self._ct.handle_sourceType(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_keyword(self, element):
        element_type = 'keyword'
        parsed = self._ct.handle_controlledVocabulary(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_project(self, element):
        element_type = 'project'
        parsed = self._ct.handle_controlledVocabulary(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_data_format(self, element):
        element_type = 'dataFormat'  # noqa
        parsed = self._st.handle_dataFormat(element)
        self.metadata.update(parsed)

    def _parse_data_type(self, element):
        element_type = 'dataType'  # noqa
        parsed = self._st.handle_dataType(element)
        self.metadata.update(parsed)

    def _parse_date(self, element):
        element_type = 'date'
        parsed = self._ct.handle_dateTypeFormatted(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_timeCoverage(self, element):  # noqa
        element_type = 'timeCoverage'
        parsed = self._ct.handle_timeCoverageType(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_variableMap(self, element):  # noqa
        element_type = 'variableMap'
        parsed = self._ct.handle_variableMap(element)
        self.metadata.setdefault(element_type, []).append(parsed)

    def _parse_variables(self, element):
        element_type = 'variables'
        parsed = self._ct.handle_variables(element)
        for variable in parsed['variables']:
            var_name = variable['name']
            variable.pop('name', None)
            self.metadata.setdefault(element_type, {})[var_name] = variable
