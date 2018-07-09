# Copyright (c) 2013-2015 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Tools for data conversion and presentation."""

import numpy as np


def get_wind_components(speed, wdir):
    r"""Calculate the U, V wind vector components from the speed and direction.

    Parameters
    ----------
    speed : array_like
        The wind speed (magnitude)
    wdir : array_like
        The wind direction, specified as the direction from which the wind is
        blowing, with 0 being North.

    Returns
    -------
    u, v : tuple of array_like
        The wind components in the X (East-West) and Y (North-South)
        directions, respectively.

    """
    u = -speed * np.sin(wdir)
    v = -speed * np.cos(wdir)
    return u, v


def str_compare_equals_ignore_case(str1, str2):
    """Case-insensitive string comparison."""
    return str1.lower() == str2.lower()


def contains_ignore_case(target, container):
    """Calculate the U, V wind vector components from the speed and direction.

    Parameters
    ----------
    target : str
        A case-insensitive string value.
    container : array_like
        The object that is checked for containing 'target'.

    Returns
    -------
    Boolean value signifying whether case-insensitive 'target'
    is a member of 'container'

    """
    return target.lower() in [x.lower() for x in container]


def get_value_ignore_case(key, container):
    """Return a value from a dictionary using a case-insensitive lookup.

    Parameters
    ----------
    key : str
        Case insensitive key to look up
    container : dictionary
        The dictionary containing 'key'

    Returns
    -------
    The value associated with case-insensitive 'key', if it exists.

    """
    return {k.lower(): v for k, v in container.items()}[key.lower()]
