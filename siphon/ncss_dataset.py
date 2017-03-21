# Copyright (c) 2013-2015 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""
This module contains code to support reading and parsing
the dataset.xml documents from the THREDDS Data Server (TDS) netCDF Subset
Service.
"""

from __future__ import print_function

import logging

import numpy as np

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


class _Types(object):
    @staticmethod
    def handle_typed_values(val, type_name, value_type):
        if value_type == 'int':
            try:
                val = val.split()
                val = list(map(int, val))
            except ValueError:
                logging.warning('Cannot convert %s to float.', val)

        elif value_type == 'float':
            try:
                val = val.split()
                val = list(map(float, val))
            except ValueError:
                logging.warning('Cannot convert %s to float', val)
        else:
            logging.warning('%s type %s not understood.', type_name,
                            value_type)

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
                stop = npts * inc + inc
                val = np.arange(start=start, step=inc, stop=stop)
                val.tolist()

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
    r"""
    An object for holding information contained in the dataset.xml NCSS
    document.

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
        r"""
        Initialize a NCSSDataset object.

        Parameters
        ----------
        element : :class:`~xml.etree.ElementTree.Element`
            An :class:`~xml.etree.ElementTree.Element` representing the top level node of an
            NCSS dataset.xml doc
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
            logging.warning(msg)

    def _parse_element(self, element):
        element_name = element.tag

        parser = dict(gridSet=self._parse_gridset, axis=self._parse_axis,
                      coordTransform=self._parse_coordTransform,
                      LatLonBox=self._parse_LatLonBox, TimeSpan=self._parse_TimeSpan,
                      AcceptList=self._parse_AcceptList,
                      featureDataset=self._parse_featureDataset, variable=self._parse_variable)

        try:
            parser[element_name](element)
        except KeyError:
            logging.warning('No parser found for element %s', element_name)

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
                logging.warning('Unknown child in %s: %s', element_name, child_name)
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
                logging.warning('Cannot have grid=%s and point=%s', grid, point)

    def _parse_featureDataset(self, element):  # noqa
        handler = self._get_handler(element.tag)
        self.featureDataset = handler(element)

    def _parse_variable(self, element):
        handler = self._get_handler(element.tag)
        tmp = handler(element)
        name = tmp['name']
        tmp = tmp.pop('name', None)
        self.variables[name] = tmp
