import socket
import struct 
import numpy as np
import zlib 
import matplotlib.pyplot as plt

ADDE_HOST = "adde.ucar.edu"

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
#    observation = bytearray("RTIMAGES GE-VIS 0 AC  700 864 X 700 864  BAND=1 "
#    "LMAG=-2 EMAG=-2 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X "
#    "TIME=X X I CAL=X VERSION=1")
    observation = bytearray("RTIMAGES GE-VIS 0 AC  2726 1732 X 2726 1732  BAND=1 "
    "LMAG=-2 EMAG=-2 TRACE=0 SPAC=1 UNIT=BRIT NAV=X AUX=YES TRACKING=0 DOC=X "
    "TIME=X X I CAL=X VERSION=1")
    msg = version + ipa + port + service + ipa + port + ipa2 + user \
    + empty_byte + project + passwd + service + a + b + zero_pad + observation 
    return msg

def display_data(data):
    '''Unpack the data and display the image'''
    meta = [0] * 65
    for i in range(65):
        meta[i] = struct.unpack('i', data[3 + i*4] + data[2 + i*4] 
                                + data[1+ i*4] + data[0 + i*4])[0]

    # i = 0 number of bytes
    # i = 4 year day
    # i = 9 num lines (rows)
    # i = 10 num elements (columns)
    # i = 14 spectral bands
    # i = 34 data location?
    # i = 64 comments

    numline = meta[9]
    numele = meta[10]
    datLoc = meta[34]
    numComments = meta[64]
    navLoc = meta[35]
    compressedDataStart = numComments * 80 + datLoc
    navbytes = datLoc - navLoc
    position = navLoc + navbytes
    startdata = compressedDataStart - position + 10
    image = data[datLoc:(datLoc + numline * numele)]
    image2 = np.fromstring(image, dtype='uint8')
    image3 = np.reshape(image2, (numline,numele))
    plt.imshow(image3)

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
