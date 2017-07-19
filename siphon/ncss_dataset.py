# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Support reading and parsing the dataset.xml documents from the netCDF Subset Service."""

from __future__ import print_function

import logging

import numpy as np

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)
log.addHandler(logging.StreamHandler())


class _Types(object):
    @staticmethod
    def handle_typed_values(val, type_name, value_type):
        """Translate typed values into the appropriate python object.

        Takes an element name, value, and type and returns a list
        with the string value(s) properly converted to a python type.

        TypedValues are handled in ucar.ma2.DataType in netcdfJava
        in the DataType enum. Possibilities are:

            "boolean"
            "byte"
            "char"
            "short"
            "int"
            "long"
            "float"
            "double"
            "Sequence"
            "String"
            "Structure"
            "enum1"
            "enum2"
            "enum4"
            "opaque"
            "object"

        All of these are values written as strings in the xml, so simply
        applying int, float to the values will work in most cases (i.e.
        the TDS encodes them as string values properly).

        Examle XML element:

        <attribute name="scale_factor" type="double" value="0.0010000000474974513"/>

        Parameters
        ----------
        val : string
            The string representation of the value attribute of the xml element

        type_name : string
            The string representation of the name attribute of the xml element

        value_type : string
            The string representation of the type attribute of the xml element

        Returns
        -------
        val : list
            A list containing the properly typed python values.

        """
        if value_type in ['byte', 'short', 'int', 'long']:
            try:
                val = val.split()
                val = list(map(int, val))
            except ValueError:
                log.warning('Cannot convert %s to int. Keeping type as str.', val)
        elif value_type in ['float', 'double']:
            try:
                val = val.split()
                val = list(map(float, val))
            except ValueError:
                log.warning('Cannot convert %s to float. Keeping type as str.', val)
        elif value_type == 'boolean':
            try:
                # special case for boolean type
                val = val.split()
                # values must be either true or false
                for potential_bool in val:
                    if potential_bool not in ['true', 'false']:
                        raise ValueError
                val = [True if bool == 'true' else False for bool in val]
            except ValueError:
                msg = 'Cannot convert values %s to boolean.'
                msg += ' Keeping type as str.'
                log.warning(msg, val)
        elif value_type == 'String':
            # nothing special for String type
            pass
        else:
            # possibilities - Sequence, Structure, enum, opaque, object,
            # and char.
            # Not sure how to handle these as I do not have an example
            # of how they would show up in dataset.xml
            log.warning('%s type %s not understood. Keeping as String.',
                        type_name, value_type)

        if not isinstance(val, list):
            val = [val]

        return val

    def handle_attribute(self, element):  # noqa
        type_name = 'attribute'
        attribute_type = None
        if 'type' in element.attrib:
            attribute_type = element.attrib['type']

        name = element.attrib['name']
        val = element.attrib['value']
        if attribute_type:
            val = self.handle_typed_values(val, type_name, attribute_type)

        return {name: val}

    def handle_values(self, element, value_type=None):  # noqa
        type_name = 'value'
        val = element.text
        if val:
            if value_type:
                val = self.handle_typed_values(val, type_name, value_type)
            else:
                val = val.split()
        else:
            increment_attrs = ['start', 'increment', 'npts']
            element_attrs = list(element.attrib.keys())
            increment_attrs.sort()
            element_attrs.sort()
            if increment_attrs == element_attrs:
                start = float(element.attrib['start'])
                inc = float(element.attrib['increment'])
                npts = float(element.attrib['npts'])
                val = start + np.arange(npts) * inc
                val = val.tolist()

        return {'values': val}

    @staticmethod
    def handle_projectionBox(element):  # noqa
        type_name = 'projectionBox'
        pb = {}
        if element.tag == type_name:
            for child in element:
                pb[child.tag] = float(child.text)

        return {type_name: pb}

    @staticmethod
    def handle_axisRef(element):  # noqa
        return element.attrib['name']

    @staticmethod
    def handle_coordTransRef(element):  # noqa
        # type_name = "coordTransRef"
        return {'coordTransRef': element.attrib['name']}

    def handle_grid(self, element):
        grid = {}
        for attr in element.attrib:
            grid[attr] = element.attrib[attr]

        attrs = {}
        for attribute in element:
            attrs.update(self.handle_attribute(attribute))

        grid['attributes'] = attrs

        return grid

    @staticmethod
    def handle_parameter(element):
        name = element.attrib['name']
        value = element.attrib['value'].strip()
        return {name: value}

    @staticmethod
    def handle_featureDataset(element):  # noqa
        fd = {}
        for attr in element.attrib:
            fd[attr] = element.attrib[attr]
        return fd

    def handle_variable(self, element):
        return self.handle_grid(element)


class NCSSDataset(object):
    """Hold information contained in the dataset.xml NCSS document.

    In general, if a dataset.xml NCSS document is missing the information
    needed to construct an attribute, that attribute will not show up as
    part of the `NCSSDataset` object.

    Note that only gridded ncss datasets may contain the attributes
    `gridsets`, `axes`, `coordinate_transforms`, and `lat_lon_box`.

    Attributes
    ----------
    variables : dict[str, str]
        A dictionary of variables

    time_span : dict[str, datetime.datetime]
        A dictionary holding the beginning and ending iso time strings which
        define the temporal bounds of the dataset

     featureDataset : dict[str, str]
        A dictionary containing the type ["grid", "point"] and location ["url"]
        of the dataset

    accept_list : dict[str, list[str]]
        A dictionary holding the types of valid returns of the dataset by
        access method [Grid, GridAsPoint, PointFeatureCollection]

    gridsets : dict[str, set[str]]
        A dictionary of gridSets contained within the dataset

    axes : dict[str, object]
        A dictionary of coordinate axes

    coordinate_transforms : dict[str, object]
        A dictionary of coordinate transforms

    lat_lon_box : dict[str, float]
        A dictionary holding the north, south, east, and west latitude and
        longitude bounds of the dataset (in degree_east, degree_north)

    """

    def __init__(self, element):
        """Initialize a NCSSDataset object.

        Parameters
        ----------
        element : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing the top level
            node of an NCSS dataset.xml doc

        """
        self._types = _Types()
        self._types_methods = _Types.__dict__

        self.gridsets = {}
        self.variables = {}
        self.axes = {}
        self.coordinate_transforms = {}
        self.accept_list = {}

        self.lat_lon_box = None
        self.time_span = None
        self.featureDataset = None

        element_name = element.tag

        if element_name == 'gridDataset' or element_name == 'capabilities':

            self.featureDataset = {'type': 'grid',
                                   'url': element.attrib['location']}
            for child in element:
                self._parse_element(child)

        else:
            self._parse_element(element)

        things_to_del = []
        for thing in self.__dict__:
            if not (thing.startswith('_') or thing.startswith('__')):
                if not getattr(self, thing):
                    things_to_del.append(thing)

        for thing in things_to_del:
            delattr(self, thing)

    def _get_handler(self, handler_name):
        handler_name = 'handle_' + handler_name
        if handler_name in self._types_methods:
            return getattr(self._types, handler_name)
        else:
            msg = 'cannot find handler for element {}'.format(handler_name)
            log.warning(msg)

    def _parse_element(self, element):
        element_name = element.tag

        parser = {'gridSet': self._parse_gridset, 'axis': self._parse_axis,
                  'coordTransform': self._parse_coordTransform,
                  'LatLonBox': self._parse_LatLonBox, 'TimeSpan': self._parse_TimeSpan,
                  'AcceptList': self._parse_AcceptList,
                  'featureDataset': self._parse_featureDataset,
                  'variable': self._parse_variable}

        try:
            parser[element_name](element)
        except KeyError:
            log.warning('No parser found for element %s', element_name)

    def _parse_gridset(self, element):
        element_name = element.tag
        gridset_name = element.attrib['name']
        grid_set = {}
        for child in element:
            child_name = child.tag
            handler = self._get_handler(child_name)
            if child_name in ['projectionBox', 'coordTransRef']:
                grid_set.update(handler(child))
            elif child_name in ['axisRef']:
                grid_set.setdefault(child_name, []).append(handler(child))
            elif child_name in ['grid']:
                tmp = handler(child)
                grid_name = tmp['name']
                tmp.pop('name', None)
                grid_set.setdefault(child_name, {})[grid_name] = tmp
                self.variables[grid_name] = tmp
            else:
                log.warning('Unknown child in %s: %s', element_name, child_name)
                grid_set[child.tag] = 'not handled by _parse_gridset'

        self.gridsets.update({gridset_name: grid_set})

    def _parse_axis(self, element):
        # element_name = element.tag
        axis_name = element.attrib['name']
        axis = {}
        for attr in element.attrib:
            if attr != 'name':
                axis[attr] = element.attrib[attr]
        if 'shape' in axis:
            typed_vals = self._types.handle_typed_values(axis['shape'], 'shape', 'int')
            axis['shape'] = typed_vals

        attrs = []
        for child in element:
            child_name = child.tag
            handler = self._get_handler(child_name)
            attrs.append(handler(child))

        if attrs:
            axis['attributes'] = attrs

        self.axes.update({axis_name: axis})

    def _parse_coordTransform(self, element):  # noqa
        coord_trans = {}
        name = element.attrib['name']
        for attr in element.attrib:
            if attr != 'name':
                coord_trans[attr] = element.attrib[attr]

        params = {}
        for child in element:
            child_name = child.tag
            handler = self._get_handler(child_name)
            params.update(handler(child))

        if params:
            coord_trans['parameters'] = params

        self.coordinate_transforms.update({name: coord_trans})

    def _parse_LatLonBox(self, element):  # noqa
        llb = {}
        for child in element:
            llb[child.tag] = float(child.text)
        self.lat_lon_box = llb

    def _parse_TimeSpan(self, element):  # noqa
        ts = {}
        for child in element:
            ts[child.tag] = child.text

        self.time_span = ts

    def _parse_AcceptList(self, element):  # noqa
        grid_req_types = ['Grid', 'GridAsPoint']
        # check if station (i.e.
        check = True
        grid = False
        point = False

        for child in element:
            request_type = child.tag
            if check:
                if request_type in grid_req_types:
                    grid = True
                else:
                    point = True
                check = False

            if point:
                # this is a PointFeatureCollection ncss
                return_type = child.text
                self.accept_list.setdefault('PointFeatureCollection',
                                            []).append(return_type)
            elif grid:
                # this is a grid ncss
                for grandchild in child:
                    return_type = grandchild.text
                    self.accept_list.setdefault(request_type,
                                                []).append(return_type)
            else:
                log.warning('Cannot have grid=%s and point=%s', grid, point)

    def _parse_featureDataset(self, element):  # noqa
        handler = self._get_handler(element.tag)
        self.featureDataset = handler(element)

    def _parse_variable(self, element):
        handler = self._get_handler(element.tag)
        tmp = handler(element)
        name = tmp['name']
        tmp = tmp.pop('name', None)
        self.variables[name] = tmp
