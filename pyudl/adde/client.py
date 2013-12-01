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

import projection
from projection import *

reload(projection)
from projection import *

ADDE_HOST = "adde.ucar.edu"

DEGREES_TO_RADIANS = np.pi/180.

# projections coming back from ADDE
MERC =  0x4D455243
TANC =  0x54414E43

projections = {MERC : (Mercator, ccrs.Mercator), \
               TANC : (Tangent_Cone, ccrs.LambertConformal)}

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
    #observation = bytearray("GINIEAST GPR1KVIS -40 AC  960 960 X 640 640  BAND=1 LMAG=-3 EMAG=-3 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X TIME=X X I CAL=X VERSION=1")
    observation = bytearray("GINIWEST GHR1KVIS -40 AC  1040 1120 X 682 746  BAND=1 LMAG=-3 EMAG=-3 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X TIME=X X I CAL=X VERSION=1")
    # observation = bytearray("GINIEAST GE1KVIS -40 AC  2560 2560 X 854 854  BAND=1 LMAG=-6 EMAG=-6 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X TIME=X X I CAL=X VERSION=1")
    msg = version + ipa + port + service + ipa + port + ipa2 + user \
    + empty_byte + project + passwd + service + a + b + zero_pad \
    + observation 
    return msg

def area_coord_to_image_coord(m,coords):
    '''Convert ADDDE area cordinated to image coordinates '''
    # how does one destructure in python?
    x,y = coords
    line = 0 
    if (m.line_flipped):
        line = m.line_offset - x
    else:
        line = x

    u = m.start_img_line \
    + (m.res_line * (line - m.start_line))/m.mag_line
    v = m.start_img_ele + (m.res_ele * (y - m.start_ele))/m.mag_ele
    return u,v

def calc_extents(m,proj):
    '''Convert ADDE cordinates to lat/lon'''
    # I need lisp!
    extents = ((0,0),(m.num_line,0),(0,m.num_ele),
               (m.num_line,m.num_ele))
    area_coord_to_image_coordp = partial(area_coord_to_image_coord,m)
    print(extents)
    imagec =  map(area_coord_to_image_coordp,extents)
    print(imagec)
    latlons = map(proj.to_lat_lon,imagec)
    print(latlons)
    return tuple(latlons)


def parse_metadata(data):
    '''Parse ADDE metadata'''

    meta = [0] * 65
    for i in range(65):
        meta[i] = struct.unpack('i', data[3 + i*4] + data[2 + i*4] 
                                + data[1+ i*4] + data[0 + i*4])[0]

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

    m = parse_metadata(data)
    pprint(vars(m))    

    #compressedDataStart = num_comments * 80 + data_loc
    nav_bytes = m.data_loc - m.nav_loc
    #Going to need polymorphism here eventually

    d = data[m.nav_loc:(m.nav_loc + nav_bytes)]

    nav = [0] *  (nav_bytes/4)
    for i in range(nav_bytes/4):
        nav[i] = struct.unpack('i', d[3 + i*4] + d[2 + i*4] 
                               + d[1 + i*4] + d[0 + i*4])[0]

    print("nav[0] " + str(nav[0]))
    print("nav[1] " + str(nav[1]))

    constr1,constr2 = projections[nav[1]]

    proj = constr1(nav)      
    
    ll,ul,lr,ul = calc_extents(m,proj)
    print(ll,ul,lr,ul)
    # position = m.nav_loc + nav_bytes
    #startdata = compressedDataStart - position + 10
    image = data[m.data_loc:(m.data_loc + m.num_line * m.num_ele)]
    image2 = np.fromstring(image, dtype='uint8')
    img = np.reshape(image2, (m.num_line,m.num_ele))
    img2 = toimage(img)

#    myproj = constr2(secant_latitudes=(25, 25) )
    myproj = constr2()
    fig = plt.figure(figsize=(12, 12))
    extents = myproj.transform_points(ccrs.Geodetic(),
                                    np.array([ll[1], ul[1]]),
                                    np.array([ll[0], ul[0]]))

    img_extents = (extents[0][0], extents[1][0], extents[0][1], 
                   extents[1][1] ) 

    ax = plt.axes(projection=myproj)
    ax.set_extent([ll[1] - 3 , ul[1] + 3, ll[0] - 3, ul[0] + 3],
                  ccrs.Geodetic())

    # image data coming from server, code not shown
    ax.imshow(img2, origin='upper', extent=img_extents, 
              transform=myproj, cmap='gray')

    ax.set_xmargin(0.05)
    ax.set_ymargin(0.10)

    ax.coastlines(resolution='50m', color='black', linewidth=1)
    ax.gridlines()
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
