import struct 
import numpy as np

DEGREES_TO_RADIANS = np.pi/180.

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


class Mercator:
    def __init__(self, data, metadata):
        nav_bytes = metadata.data_loc - metadata.nav_loc
        d = data[metadata.nav_loc:(metadata.nav_loc + nav_bytes)]

        nav = [0] *  (nav_bytes/4)
        for i in range(nav_bytes/4):
            nav[i] = struct.unpack('i', d[3 + i*4] + d[2 + i*4] 
                                   + d[1 + i*4] + d[0 + i*4])[0]

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

        self.xrow = xrow
        self.xcol = xcol
        self.xlat1 = xlat1
        self.xspace = xspace
        self.xqlon = xqlon
        self.r = r
        self.iwest = iwest
        self.xblat = xblat
        self.xblon = xblon
        self.leftlon = leftlon

    def to_lat_lon(self, coord):
        '''Convert image coordinates to lat/lon'''
        x,y = coord
        xldif = self.xrow - x
        xedif = self.xcol - y
        xrlon = self.iwest * xedif/self.xblon
        xlon = xrlon + self.xqlon
        xrlat = np.arctan(np.exp(xldif/self.xblat))
        xlat = (xrlat/DEGREES_TO_RADIANS - 45.) * 2. + self.xlat1
        if (xlon > (360. + self.leftlon) or xlon < self.leftlon):
            lat = np.nan
            lon = np.nan
        else:
            lat = xlat
            if (xlon > 180.0):
                xlon = xlon - 360.0
            if (xlon < -180.0):
                xlon = xlon + 360.0        
        if (self.iwest == 1):
            xlon = -xlon
        return xlat,xlon
