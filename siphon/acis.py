import json
import urllib.request
import urllib.parse
import json
import socket

def acisRequest(method, params):
    """
    
    This function will make a request to the ACIS Web Services API for data
    based on the given method (StnMeta,StnData,MultiStnData,GridData,General)
    and parameters string. Information about the parameters can be obtained at:
    http://www.rcc-acis.org/docs_webservices.html

    If a connection to the API fails, then it returns False. A failed request
    will have an error text in the return data produced by the remote API.

    Parameters
    ----------
    method - The Web Services request method (StnMeta, StnData, MultiStnData, etc)
    params - A dictionary of parameters (see API documentation)

    Returns
    ----------
    Connection Success: A dictionary that is derived from JSON data from the remote API
    Connection Failure: False

    """
    params = json.dumps(params).encode('utf8')

    base_url = 'http://data.rcc-acis.org/'  # ACIS Web API URL

    req = urllib.request.Request(base_url+method,
                          params, {'Content-Type': 'application/json'})
    if method == 'MultiStnData':
        timeout=300
    else:
        timeout=60

    try:
        response = urllib.request.urlopen(req, timeout=timeout)  # 10-Minute Timeout
        return json.loads(response.read())
    except urllib.request.HTTPError as error:
        if error.code == 400:
            print(error.msg)
        print(error)
        return False

    except socket.timeout:
        print("Connection Timeout")
        return False  # Failed This Time
