import struct 
import numpy as np

DEGREES_TO_RADIANS = np.pi/180.
EARTH_RADIUS = 6371.2

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
    def __init__(self, nav):

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


class Tangent_Cone:
    def __init__(self, nav):
        self.lin0  = nav[2]/10000.
        self.ele0  = nav[3]/10000.
        self.scale = nav[4]/10000.
        self.lat0  = nav[5]/10000.
        self.lon0  = -nav[6]/10000 * DEGREES_TO_RADIANS

        if (self.lat0 < 0):
            self.colat0 = np.pi/2. + self.lat0*DEGREES_TO_RADIANS
        else:
            self.colat0 = np.pi/2. - self.lat0*DEGREES_TO_RADIANS

        self.coscl = np.cos(self.colat0);
        self.tancl = np.tan(self.colat0);
        self.tancl2 = np.tan(self.colat0/2.);
        self.mxtheta = np.pi*self.coscl;

    def to_lat_lon(self, coord):
        x,y = coord

        d_lin = x - self.lin0;
        d_ele = y - self.ele0;

        if (np.abs(d_lin) < 0.01 and np.abs(d_ele) < 0.01):
            radius = 0.0
            theta_rh = 0.0
        else:
            dx = self.scale*(d_lin)
            dy = self.scale*(d_ele)
            radius = np.sqrt(dx*dx + dy*dy)
            theta_rh = np.arctan2(dy, dx)

        if (self.lat0 < 0.):
            if (theta_rh <= 0.):
                theta = np.pi - np.abs(theta_rh)
            else:
                theta = -1.*(np.pi- np.abs(theta_rh))
        else:
            theta = theta_rh;

        if (theta <= -self.mxtheta or theta > self.mxtheta):
            lat = np.nan
            lon = np.nan
        else:
            lon = self.lon0 + theta/self.coscl
            if (lon <= -np.pi):
                lon = lon + 2.*np.pi
            if (lon > np.pi):
                lon = lon - 2.*np.pi

            colat = 2.* np.arctan(self.tancl2 \
                                  *np.power(radius/ \
                                          (EARTH_RADIUS*self.tancl),
                                        1./self.coscl))

            # convert to degrees
            lon = lon/DEGREES_TO_RADIANS
            lat = 90. - colat/DEGREES_TO_RADIANS
            
            if (self.lat0 < 0):
                lat = -1*lat 
            lon = lon
        
        return lat,lon
