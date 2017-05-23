# Copyright (c) 2014-2016 University Corporation for Atmospheric Research/Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT
"""Handle binary stream returns in NCStream format."""

from __future__ import print_function

from collections import OrderedDict
import itertools
import logging
import zlib

import numpy as np

from . import cdmrfeature_pb2 as cdmrf
from . import ncStream_pb2 as stream  # noqa

MAGIC_HEADER = b'\xad\xec\xce\xda'
MAGIC_DATA = b'\xab\xec\xce\xba'
MAGIC_DATA2 = b'\xab\xeb\xbe\xba'
MAGIC_VDATA = b'\xab\xef\xfe\xba'
MAGIC_VEND = b'\xed\xef\xfe\xda'
MAGIC_ERR = b'\xab\xad\xba\xda'

MAGIC_HEADERCOV = b'\xad\xed\xde\xda'
MAGIC_DATACOV = b'\xab\xed\xde\xba'

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())  # Python 2.7 needs a handler set
log.setLevel(logging.WARNING)


#
# NCStream handling
#
def read_ncstream_data(fobj):
    """Handle reading an NcStream v1 data block from a file-like object."""
    data = read_proto_object(fobj, stream.Data)
    if data.dataType in (stream.STRING, stream.OPAQUE) or data.vdata:
        log.debug('Reading string/opaque/vlen')
        num_obj = read_var_int(fobj)
        log.debug('Num objects: %d', num_obj)
        blocks = [read_block(fobj) for _ in range(num_obj)]
        if data.dataType == stream.STRING:
            blocks = [b.decode('utf-8', errors='ignore') for b in blocks]

        # Again endian isn't coded properly
        dt = data_type_to_numpy(data.dataType).newbyteorder('>')
        if data.vdata:
            return np.array([np.frombuffer(b, dtype=dt) for b in blocks])
        else:
            return np.array(blocks, dtype=dt)
    elif data.dataType in _dtypeLookup:
        log.debug('Reading array data')
        bin_data = read_block(fobj)
        log.debug('Binary data: %s', bin_data)

        # Hard code to big endian for now since it's not encoded correctly
        dt = data_type_to_numpy(data.dataType).newbyteorder('>')

        # Handle decompressing the bytes
        if data.compress == stream.DEFLATE:
            bin_data = zlib.decompress(bin_data)
            assert len(bin_data) == data.uncompressedSize
        elif data.compress != stream.NONE:
            raise NotImplementedError('Compression type {0} not implemented!'.format(
                data.compress))

        # Turn bytes into an array
        return reshape_array(data, np.frombuffer(bin_data, dtype=dt))
    elif data.dataType == stream.STRUCTURE:
        sd = read_proto_object(fobj, stream.StructureData)

        # Make a datatype appropriate to the rows of struct
        endian = '>' if data.bigend else '<'
        dt = np.dtype([(endian, np.void, sd.rowLength)])

        # Turn bytes into an array
        return reshape_array(data, np.frombuffer(sd.data, dtype=dt))
    elif data.dataType == stream.SEQUENCE:
        log.debug('Reading sequence')
        blocks = []
        magic = read_magic(fobj)
        while magic != MAGIC_VEND:
            if magic == MAGIC_VDATA:
                log.error('Bad magic for struct/seq data!')
            blocks.append(read_proto_object(fobj, stream.StructureData))
            magic = read_magic(fobj)
        return data, blocks
    else:
        raise NotImplementedError("Don't know how to handle data type: {0}".format(
            data.dataType))


def read_ncstream_data2(fobj):
    """Handle reading an NcStream v2 data block from a file-like object."""
    data = read_proto_object(fobj, stream.DataCol)
    return datacol_to_array(data)


def read_ncstream_err(fobj):
    """Handle reading an NcStream error from a file-like object and raise as error."""
    err = read_proto_object(fobj, stream.Error)
    raise RuntimeError(err.message)


ncstream_table = {MAGIC_HEADER: lambda f: read_proto_object(f, stream.Header),
                  MAGIC_DATA: read_ncstream_data,
                  MAGIC_DATA2: read_ncstream_data2,
                  MAGIC_ERR: read_ncstream_err}


def read_ncstream_messages(fobj):
    """Read a collection of NcStream messages from a file-like object."""
    return read_messages(fobj, ncstream_table)


#
# CDMRemoteFeature handling
#
cdmrf_table = {MAGIC_HEADERCOV: lambda f: read_proto_object(f, cdmrf.CoverageDataset),
               MAGIC_DATACOV: lambda f: read_proto_object(f, cdmrf.CoverageDataResponse),
               MAGIC_DATA2: read_ncstream_data2,  # For coordinates
               MAGIC_ERR: read_ncstream_err}


def read_cdmrf_messages(fobj):
    """Read a collection of CDMRemoteFeature messages from a file-like object."""
    return read_messages(fobj, cdmrf_table)


#
# General Utilities
#
def read_messages(fobj, magic_table):
    """Read messages from a file-like object until stream is exhausted."""
    messages = []

    while True:
        magic = read_magic(fobj)
        if not magic:
            break

        func = magic_table.get(magic)
        if func is not None:
            messages.append(func(fobj))
        else:
            log.error('Unknown magic: ' + str(' '.join('{0:02x}'.format(b)
                                                       for b in bytearray(magic))))

    return messages


def read_proto_object(fobj, klass):
    """Read a block of data and parse using the given protobuf object."""
    log.debug('%s chunk', klass.__name__)
    obj = klass()
    obj.ParseFromString(read_block(fobj))
    log.debug('Header: %s', str(obj))
    return obj


def read_magic(fobj):
    """Read magic bytes.

    Parameters
    ----------
    fobj : file-like object
        The file to read from.

    Returns
    -------
    bytes
        magic byte sequence read

    """
    return fobj.read(4)


def read_block(fobj):
    """Read a block.

    Reads a block from a file object by first reading the number of bytes to read, which must
    be encoded as a variable-byte length integer.

    Parameters
    ----------
    fobj : file-like object
        The file to read from.

    Returns
    -------
    bytes
        block of bytes read

    """
    num = read_var_int(fobj)
    log.debug('Next block: %d bytes', num)
    return fobj.read(num)


def process_vlen(data_header, array):
    """Process vlen coming back from NCStream v2.

    This takes the array of values and slices into an object array, with entries containing
    the appropriate pieces of the original array. Sizes are controlled by the passed in
    `data_header`.

    Parameters
    ----------
    data_header : Header
    array : :class:`numpy.ndarray`

    Returns
    -------
    ndarray
        object array containing sub-sequences from the original primitive array

    """
    source = iter(array)
    return np.array([np.fromiter(itertools.islice(source, size), dtype=array.dtype)
                     for size in data_header.vlens])


def datacol_to_array(datacol):
    """Convert DataCol from NCStream v2 into an array with appropriate type.

    Depending on the data type specified, this extracts data from the appropriate members
    and packs into a :class:`numpy.ndarray`, recursing as necessary for compound data types.

    Parameters
    ----------
    datacol : DataCol

    Returns
    -------
    ndarray
        array containing extracted data

    """
    if datacol.dataType == stream.STRING:
        arr = np.array(datacol.stringdata, dtype=np.object)
    elif datacol.dataType == stream.OPAQUE:
        arr = np.array(datacol.opaquedata, dtype=np.object)
    elif datacol.dataType == stream.STRUCTURE:
        members = OrderedDict((mem.name, datacol_to_array(mem))
                              for mem in datacol.structdata.memberData)
        log.debug('Struct members:\n%s', str(members))

        # str() around name necessary because protobuf gives unicode names, but dtype doesn't
        # support them on Python 2
        dt = np.dtype([(str(name), arr.dtype) for name, arr in members.items()])
        log.debug('Struct dtype: %s', str(dt))

        arr = np.empty((datacol.nelems,), dtype=dt)
        for name, arr_data in members.items():
            arr[name] = arr_data
    else:
        # Make an appropriate datatype
        endian = '>' if datacol.bigend else '<'
        dt = data_type_to_numpy(datacol.dataType).newbyteorder(endian)

        # Turn bytes into an array
        arr = np.frombuffer(datacol.primdata, dtype=dt)
        if arr.size != datacol.nelems:
            log.warning('Array size %d does not agree with nelems %d',
                        arr.size, datacol.nelems)
        if datacol.isVlen:
            arr = process_vlen(datacol, arr)
            if arr.dtype == np.object_:
                arr = reshape_array(datacol, arr)
            else:
                # In this case, the array collapsed, need different resize that
                # correctly sizes from elements
                shape = tuple(r.size for r in datacol.section.range) + (datacol.vlens[0],)
                arr = arr.reshape(*shape)
        else:
            arr = reshape_array(datacol, arr)
    return arr


def reshape_array(data_header, array):
    """Extract the appropriate array shape from the header.

    Can handle taking a data header and either bytes containing data or a StructureData
    instance, which will have binary data as well as some additional information.

    Parameters
    ----------
    array : :class:`numpy.ndarray`
    data_header : Data

    """
    shape = tuple(r.size for r in data_header.section.range)
    if shape:
        return array.reshape(*shape)
    else:
        return array


# STRUCTURE = 8;
# SEQUENCE = 9;
_dtypeLookup = {stream.CHAR: 'S1', stream.BYTE: 'b', stream.SHORT: 'i2',
                stream.INT: 'i4', stream.LONG: 'i8', stream.FLOAT: 'f4',
                stream.DOUBLE: 'f8', stream.STRING: 'O',
                stream.ENUM1: 'B', stream.ENUM2: 'u2', stream.ENUM4: 'u4',
                stream.OPAQUE: 'O', stream.UBYTE: 'B', stream.USHORT: 'u2',
                stream.UINT: 'u4', stream.ULONG: 'u8'}


def data_type_to_numpy(datatype, unsigned=False):
    """Convert an ncstream datatype to a numpy one."""
    basic_type = _dtypeLookup[datatype]

    if datatype in (stream.STRING, stream.OPAQUE):
        return np.dtype(basic_type)

    if unsigned:
        basic_type = basic_type.replace('i', 'u')
    return np.dtype('=' + basic_type)


def struct_to_dtype(struct):
    """Convert a Structure specification to a numpy structured dtype."""
    # str() around name necessary because protobuf gives unicode names, but dtype doesn't
    # support them on Python 2
    fields = [(str(var.name), data_type_to_numpy(var.dataType, var.unsigned))
              for var in struct.vars]
    for s in struct.structs:
        fields.append((str(s.name), struct_to_dtype(s)))

    log.debug('Structure fields: %s', fields)
    dt = np.dtype(fields)
    return dt


def unpack_variable(var):
    """Unpack an NCStream Variable into information we can use."""
    # If we actually get a structure instance, handle turning that into a variable
    if var.dataType == stream.STRUCTURE:
        return None, struct_to_dtype(var), 'Structure'
    elif var.dataType == stream.SEQUENCE:
        log.warning('Sequence support not implemented!')

    dt = data_type_to_numpy(var.dataType, var.unsigned)
    if var.dataType == stream.OPAQUE:
        type_name = 'opaque'
    elif var.dataType == stream.STRING:
        type_name = 'string'
    else:
        type_name = dt.name

    if var.data:
        log.debug('Storing variable data: %s %s', dt, var.data)
        if var.dataType == stream.STRING:
            data = var.data
        else:
            # Always sent big endian
            data = np.fromstring(var.data, dtype=dt.newbyteorder('>'))
    else:
        data = None

    return data, dt, type_name


_attrConverters = {stream.Attribute.BYTE: np.dtype('>b'),
                   stream.Attribute.SHORT: np.dtype('>i2'),
                   stream.Attribute.INT: np.dtype('>i4'),
                   stream.Attribute.LONG: np.dtype('>i8'),
                   stream.Attribute.FLOAT: np.dtype('>f4'),
                   stream.Attribute.DOUBLE: np.dtype('>f8')}


def unpack_attribute(att):
    """Unpack an embedded attribute into a python or numpy object."""
    if att.unsigned:
        log.warning('Unsupported unsigned attribute!')

    # TDS 5.0 now has a dataType attribute that takes precedence
    if att.len == 0:  # Empty
        val = None
    elif att.dataType == stream.STRING:  # Then look for new datatype string
        val = att.sdata
    elif att.dataType:  # Then a non-zero new data type
        val = np.fromstring(att.data,
                            dtype='>' + _dtypeLookup[att.dataType], count=att.len)
    elif att.type:  # Then non-zero old-data type0
        val = np.fromstring(att.data,
                            dtype=_attrConverters[att.type], count=att.len)
    elif att.sdata:  # This leaves both 0, try old string
        val = att.sdata
    else:  # Assume new datatype is Char (0)
        val = np.array(att.data, dtype=_dtypeLookup[att.dataType])

    if att.len == 1:
        val = val[0]

    return att.name, val


def read_var_int(file_obj):
    """Read a variable-length integer.

    Parameters
    ----------
    file_obj : file-like object
        The file to read from.

    Returns
    -------
    int
        the variable-length value read

    """
    # Read all bytes from here, stopping with the first one that does not have
    # the MSB set. Save the lower 7 bits, and keep stacking to the *left*.
    val = 0
    shift = 0
    while True:
        # Read next byte
        next_val = ord(file_obj.read(1))
        val |= ((next_val & 0x7F) << shift)
        shift += 7
        if not next_val & 0x80:
            break

    return val
