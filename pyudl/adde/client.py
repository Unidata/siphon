import socket
import struct 
import numpy as np
import zlib 
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from pylab import savefig
from scipy.misc import toimage
from copy import deepcopy
from pprint import pprint
from functools import partial

ADDE_HOST = "adde.ucar.edu"

DEGREES_TO_RADIANS = np.pi/180.

class mysocket:
    '''Socket class'''

    def __init__(self, sock=None):
        '''Initialize the socket'''
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        '''Socket connection, given a host and port'''
        self.sock.connect((host, port))

    def close(self):
        '''Close the socket'''
        self.sock.close()

    def send(self, msg):
        '''Send data to the socket'''
        sent = self.sock.send(msg[0:])
        if sent == 0:
           raise RuntimeError("socket connection broken")

    def receive(self):
        '''Receive data from the socket'''
        total_data=[]
        while True:
            data = self.sock.recv(8192)
            if not data: break
            total_data.append(data)
        return ''.join(total_data)

class Metadata(object):
    pass

class Mercator(object):
    pass

def get_local_ip():
    '''Get the IP address of the local host'''
    # http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("gmail.com",80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def get_bytearray_ip(host):
    '''Given a host string, return a the IP address byte array'''
    return bytearray(np.array(socket.gethostbyname(host).split('.'), 
                             dtype = 'uint8'))

def create_msg():
    '''Create the byte array that will be sent to the server.'''
    def myzeros(n):
        '''For padding data'''
        a = []
        for i in range(n):
            a.append(0)    
        return bytearray(a)
    # ADDE version
    version = bytearray([0, 0, 0, 1])
    
    ipa = get_bytearray_ip(ADDE_HOST)

    port = bytearray([0, 0, 0, 112])
    service = bytearray("aget")
    ipa2 = get_bytearray_ip(get_local_ip())
    user = bytearray("idv")
    empty_byte = bytearray(" ")
    project = struct.pack("i", 0)
    passwd = myzeros(12)
    a  = bytearray([0, 0, 0, 146])
    b  = bytearray([0, 0, 0, 146])
    zero_pad = myzeros(116)
    # observation = bytearray("RTIMAGES GE-VIS 0 AC  700 864 X 700 864  BAND=1 "
    # "LMAG=-2 EMAG=-2 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X "
    # "TIME=X X I CAL=X VERSION=1")
    # observation = bytearray("GINICOMP GSN8KPW -1 EC 49.70000 105.00000 X 1000 1000  BAND=17 LMAG=1 EMAG=1 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X TIME=X X I CAL=X VERSION=1")
    observation = bytearray("GINIEAST GPR1KVIS -10 AC  960 960 X 640 640  BAND=1 LMAG=-3 EMAG=-3 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X TIME=X X I CAL=X VERSION=1")
    msg = version + ipa + port + service + ipa + port + ipa2 + user \
    + empty_byte + project + passwd + service + a + b + zero_pad + observation 
    return msg


def int_latlon_to_float(value):
    '''Convert integer lat/lon to float'''
    val = 0

    if (value < 0):
        val = int(-value)
    else:
        val = int(value)

    deg = float(val / 10000) 
    min = (float((val / 100) % 100)) / 60.0 
    sec = float(val % 100) / 3600.0
    value = deg + min + sec
    
    if (value < 0):
        result = -value
    else:
        result = value
    return result


def nav_mercator_parse(data, navLoc, navbytes):
    '''Parse the Mercator navigation block coming back from ADDE '''
    nav = [0] *  (navbytes/4)
    for i in range(navbytes/4):
        nav[i] = struct.unpack('i', data[3 + i*4] + data[2 + i*4] 
                                + data[1 + i*4] + data[0 + i*4])[0]

    xrow = nav[2]
    xcol = nav[3]
    xlat1 = int_latlon_to_float(nav[4])
    xspace = nav[5]/1000.
    xqlon = int_latlon_to_float(nav[6])
    r = nav[7]/1000.
    iwest = nav[10];
    if (iwest >= 0):
        iwest = 1
    xblat = r * np.cos(xlat1 * DEGREES_TO_RADIANS)/xspace
    xblon = DEGREES_TO_RADIANS * r/xspace
    leftlon = int(xqlon - 180 * iwest)

    m = Mercator()
    m.xrow = xrow
    m.xcol = xcol
    m.xlat1 = xlat1
    m.xspace = xspace
    m.xqlon = xqlon
    m.r = r
    m.iwest = iwest
    m.xblat = xblat
    m.xblon = xblon
    m.leftlon = leftlon
    return m


def area_coord_to_image_coord(m,coords):
    '''Convert ADDDE area cordinated to image coordinates '''
    # how does one destructure in python?
    x,y = coords
    line = 0 
    if (m.line_flipped):
        line = m.line_offset - x
    else:
        line = x

    u = m.start_img_line + (m.res_line * (line - m.start_line))/m.mag_line
    v = m.start_img_ele + (m.res_ele * (y - m.start_ele))/m.mag_ele
    return u,v


def to_lat_lon(merc,coord):
    '''Convert image coordinates to lat/lon'''
    x,y = coord
    xldif = merc.xrow - x
    xedif = merc.xcol - y
    xrlon = merc.iwest * xedif/merc.xblon
    xlon = xrlon + merc.xqlon
    xrlat = np.arctan(np.exp(xldif/merc.xblat))
    xlat = (xrlat/DEGREES_TO_RADIANS - 45.) * 2. + merc.xlat1
    if (xlon > (360. + merc.leftlon) or xlon < merc.leftlon):
        lat = np.nan
        lon = np.nan
    else:
        lat = xlat
        if (xlon > 180.0):
            xlon = xlon - 360.0
        if (xlon < -180.0):
            xlon = xlon + 360.0        
    if (merc.iwest == 1):
        xlon = -xlon
    return xlat,xlon


def calc_extents(m,merc):
    '''Convert ADDE cordinates to lat/lon'''
    # I need lisp!
    extents = ((0,0),(m.num_line,0),(0,m.num_ele),(m.num_ele,m.num_line))
    area_coord_to_image_coordp = partial(area_coord_to_image_coord,m)
    imagec =  map(area_coord_to_image_coordp,extents)
    to_lat_lonp = partial(to_lat_lon,merc)
    latlons = map(to_lat_lonp,imagec)
    return tuple(latlons)


def parse_metadata(meta):
    '''Parse ADDE metadata'''
    m = Metadata()
    m.num_bytes = meta[0]
    m.year_day = meta[4]
    m.start_img_line = meta[6]
    m.start_img_ele = meta[7]
    m.res_line = meta[12]
    m.res_ele = meta[13]
    m.spectral_bands = meta[34]
    m.start_line = 0
    m.start_ele = 0
    m.mag_line = 1
    m.mag_ele = 1
    m.num_line=meta[9]
    m.num_ele = meta[10]
    m.data_loc= meta[34]
    m.nav_loc = meta[35]
    m.num_comments = meta[64]
    m.line_flipped = True
    m.line_offset = m.num_line - 1
    return m


def display_data(data):
    '''Unpack the data and display the image'''
    meta = [0] * 65
    for i in range(65):
        meta[i] = struct.unpack('i', data[3 + i*4] + data[2 + i*4] 
                                + data[1+ i*4] + data[0 + i*4])[0]

    m = parse_metadata(meta)
    pprint(vars(m))    

    #compressedDataStart = num_comments * 80 + data_loc
    nav_bytes = m.data_loc - m.nav_loc
    nav = nav_mercator_parse(data[m.nav_loc:(m.nav_loc + nav_bytes)], m.nav_loc, nav_bytes)
    ll,ul,lr,ul = calc_extents(m,nav)
    position = m.nav_loc + nav_bytes
    #startdata = compressedDataStart - position + 10
    image = data[m.data_loc:(m.data_loc + m.num_line * m.num_ele)]
    image2 = np.fromstring(image, dtype='uint8')
    img = np.reshape(image2, (m.num_line,m.num_ele))
    img2 = toimage(img)

    merc = ccrs.Mercator()
    lamb = ccrs.LambertConformal()
    pc = ccrs.PlateCarree()
    fig = plt.figure(figsize=(12, 12))
    extents = merc.transform_points(ccrs.Geodetic(),
                                    np.array([ll[1], ul[1]]),
                                    np.array([ll[0], ul[0]]))

    img_extents = (extents[0][0], extents[1][0], extents[0][1], extents[1][1] ) 

    ax = plt.axes(projection=merc)
    ax.set_extent([-80, -50.5, 5, 30], ccrs.Geodetic())

    # image data coming from server, code not shown
    ax.imshow(img2, origin='upper', extent=img_extents, transform=merc, cmap='gray')

    ax.set_xmargin(0.05)
    ax.set_ymargin(0.10)

    ax.coastlines(resolution='50m', color='black', linewidth=1)
    ax.gridlines()

    savefig("/tmp/sat.png")

    plt.show() 


def view_satellite_image():
    '''High level method to view satellite imagery '''
    msg = create_msg()
    sock = mysocket()
    sock.connect("adde.ucar.edu", 112)
    sock.send(msg)
    cdata= sock.receive()
    sock.close()
    udata = zlib.decompress(cdata, 15+32)
    display_data(udata)
