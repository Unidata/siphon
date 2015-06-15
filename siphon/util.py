import requests

from io import BytesIO
from . import __version__

user_agent = 'Siphon (%s)' % __version__


def create_http_session():
    r'''Create a new HTTP session with our user-agent set.

    Returns
    -------
    session : ``requests.Session``
        The created session

    See Also
    --------
    urlopen
    '''

    ret = requests.Session()
    ret.headers['User-Agent'] = user_agent
    return ret


def urlopen(url, **kwargs):
    r'''GET a file-like object for a URL using HTTP.

    This is a thin wrapper around ``requests.get`` that returns a file-like object
    wrapped around the resulting content.

    Parameters
    ----------
    url : string
        The URL to request

    kwargs : arbitrary keyword arguments
        Additional keyword arguments to pass to ``requests.get``.

    Returns
    -------
    fobj : file-like object
        A file-like interface to the content in the response

    See Also
    --------
    http_get
    '''

    return BytesIO(create_http_session().get(url, **kwargs).content)
