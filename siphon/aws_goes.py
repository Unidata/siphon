"""
USAGE:

from datetime import datetime
from glmtools.feeds.aws import GOESArchiveDownloader, GOESProduct, save_s3_product
startdate = datetime(2018,3,27,23,59,0)
enddate = datetime(2018,3,28,0,1,0)

outpath = '/data/GLM-L2-LCFA_G16_s20180328/'

arc = GOESArchiveDownloader()
ABI_prods = arc.get_range(startdate, enddate, GOESProduct(typ='ABI',
                          channel=14, sector='conus'))
GLM_prods = arc.get_range(startdate, enddate, GOESProduct(typ='GLM'))

# for s3obj in ABI_prods:
#     save_s3_product(s3obj, outpath)
# for s3obj in GLM_prods:
#     save_s3_product(s3obj, outpath)
"""


import itertools
from tempfile import NamedTemporaryFile
import os
from datetime import datetime, timedelta

import boto3
import botocore
from botocore.client import Config
from netCDF4 import Dataset


def gen_day_chunks(start, end):
    """
    Given end > start, yield the start, then the day boundaries in between,
    and finally the end.
    """
    one_day = timedelta(days=1)
    remainder = end-start
    if remainder.total_seconds() <= 0:
        raise ValueError("end time must be larger than start time")
    last = start
    while remainder.total_seconds() > 0:
        yield last
        start_next_day = datetime(last.year, last.month, last.day) + one_day
        last = start_next_day
        remainder = end - last
    yield end


def gen_hour_chunks(start, end):
    """
    Given end > start, yield the start, then the hour boundaries in between,
    and finally the end.
    """
    one_hour = timedelta(days=0, hours=1)
    remainder = end-start
    if remainder.total_seconds() <= 0:
        raise ValueError("end time must be larger than start time")
    last = start
    while remainder.total_seconds() > 0:
        yield last
        start_next = datetime(last.year, last.month, last.day, last.hour) + one_hour
        last = start_next
        remainder = end - last
    yield end


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class GOESArchiveDownloader(object):
    def __init__(self, bucket='noaa-goes16'):
        s3 = boto3.resource('s3', config=Config(
                            signature_version=botocore.UNSIGNED,
                            user_agent_extra='Resource'))
        self._bucket = s3.Bucket(bucket)

    def _get_iter(self, start, product):
        # Set up the 'path' part, which is only the basic instrument category
        prod_prefix = product.prefix(start)
        # And the full path including the first part of the filename
        start_marker = product.with_start_time(start)
        print(prod_prefix, start_marker)
        return self._bucket.objects.filter(Marker=start_marker, Prefix=prod_prefix)

    def get_next(self, time, product):
        return next(iter(self._get_iter(time, product)))

    def get_range_in_hour_chunks(self, start, end, product):
        """ We have to go in hourly chunks because the prefix structure
            will only filter properly if we do one hour at a time. Otherwise,
            the comparison of obj.key <= end_key across hour or day boundaries
            will fail, especially for ABI products, where there is a channel to
            select.
        """
        path, prod_mode, nc_basename = product.key_components()
        print("prod_mode is", prod_mode)
        end_key = product.with_start_time(end)

        # Get a list of files that have the proper prefix up to the hour
        return list(itertools.takewhile(lambda obj: (obj.key <= end_key),
                                        self._get_iter(start, product)))

    def get_range(self, start, end, product):
        in_range = []
        for t0, t1 in pairwise(gen_day_chunks(start, end)):
            this_range = self.get_range_in_hour_chunks(t0, t1, product)
            in_range.extend(this_range)
        return in_range


class GOESProduct(object):
    def __init__(self, **kwargs):
        self.sector = 'conus'
        self.satellite = 'goes16'
        self.typ = 'ABI'
        self.channel = 1
        self.mode = 3
        self.keypath = '{prod_id}'
        self.__dict__.update(kwargs)

    def key_components(self):
        env = 'OR'
        sat = {'goes16': 'G16', 'goes17': 'G17'}[self.satellite]

        if self.typ == 'ABI':
            sectors = {'conus': 'C', 'meso1': 'M1', 'meso2': 'M2', 'full': 'F'}
            sector = sectors[self.sector]
            prod_id = 'ABI-L1b-Rad{sector}'.format(sector=sector)
            prod_code = '-M{mode}C{channel:02d}'.format(sector=sector,
                                                        mode=self.mode,
                                                        channel=self.channel)
            prod_mode = prod_id + prod_code
        elif self.typ == 'GLM':
            prod_id = 'GLM-L2-LCFA'
            prod_mode = prod_id
        else:
            raise ValueError('Unhandled data type: {}'.format(self.typ))
        path = prod_id
        nc_basename = '{env}_{prodid}_{sat}'.format(env=env, prodid=prod_mode,
                                                    sat=sat)
        return path, prod_mode, nc_basename

    def prefix(self, time):
        path, prod_mode, nc_basename = self.key_components()
        return path + '/{time:%Y/%j/%H}/'.format(time=time) + nc_basename

    def __str__(self):
        path, prod_mode, nc_basename = self.key_components()
        return path

    __repr__ = __str__

    def with_start_time(self, time):
        path, prod_mode, nc_basename = self.key_components()
        base = self.prefix(time)
        return (base + '_s{time:%Y%j%H%M%S}').format(time=time)


def netcdf_from_s3(s3obj):
    """ Download the data and open (in memory) with netCDF """
    with NamedTemporaryFile(suffix='.nc') as temp:
        # Create a temporary netCDF file to work around bug in netCDF C 4.4.1.1
        # We shouldn't actually need any file on disk.
        nc_temp = Dataset(temp.name, 'w').close()
        return Dataset(temp.name, memory=s3obj.get()['Body'].read())


def save_s3_product(s3obj, path):
    """ Save an S3 object to path. The filename is extracted from the S3 object
    it will overwrite a previous file with the same name.
    """
    obj = s3obj
    filename = obj.key.split('/')[-1]
    outfile = os.path.join(path, filename)
    print(filename)
    with open(outfile, 'wb') as f:
        data = obj.get()['Body'].read()
        f.write(data)
