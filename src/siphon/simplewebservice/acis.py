# Copyright (c) 2018 Siphon Contributors.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
"""Requests data from the ACIS Web Services API."""

import requests

from ..http_util import session_manager


def acis_request(method, params):
    """Request data from the ACIS Web Services API.

    Makes a request from the ACIS Web Services API for data
    based on a given method (StnMeta,StnData,MultiStnData,GridData,General)
    and parameters string. Information about the parameters can be obtained at:
    http://www.rcc-acis.org/docs_webservices.html

    If a connection to the API fails, then it will raise an exception. Some bad
    calls will also return empty dictionaries.

    ACIS Web Services is a distributed system! A call to the main URL can be
    delivered to any climate center running a public instance of the service.
    This makes the calls efficient, but also occasionally results in failed
    calls when a server you are directed to is having problems. Generally,
    reconnecting after waiting a few seconds will resolve a problem. If problems
    are persistent, contact ACIS developers at the High Plains Regional Climate
    Center or Northeast Regional Climate Center who will look into server
    issues.

    Parameters
    ----------
    method : str
        The Web Services request method (StnMeta, StnData, MultiStnData, GridData, General)
    params : dict
        A JSON array of parameters (See Web Services API)

    Returns
    -------
    dict[str, Any]
        A dictionary of data based on the JSON parameters

    Raises
    ------
    `AcisApiException`
        When the API is unable to establish a connection or returns
        unparsable data.

    """
    base_url = 'http://data.rcc-acis.org/'  # ACIS Web API URL

    timeout = 300 if method == 'MultiStnData' else 60

    try:
        response = session_manager.create_session().post(base_url + method, json=params,
                                                         timeout=timeout)
        return response.json()
    except requests.exceptions.Timeout as e:
        raise AcisApiException('Connection Timeout') from e
    except requests.exceptions.TooManyRedirects as e:
        raise AcisApiException('Bad URL. Check your ACIS connection method string.') from e
    except ValueError as e:
        raise AcisApiException('No data returned! The ACIS parameter dictionary'
                               'may be incorrectly formatted') from e


class AcisApiException(Exception):  # noqa: N818
    """Handle exceptions raised by the acis_request function."""

