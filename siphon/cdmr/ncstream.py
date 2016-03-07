# Copyright (c) 2013-2015 Unidata.
# Distributed under the terms of the MIT License.
# SPDX-License-Identifier: MIT

from __future__ import print_function
import itertools
import logging
import zlib

from collections import OrderedDict

import numpy as np

from . import ncStream_pb2 as stream  # noqa

MAGIC_HEADER = b'\xad\xec\xce\xda'
MAGIC_DATA = b'\xab\xec\xce\xba'
MAGIC_DATA2 = b'\xab\xeb\xbe\xba'
MAGIC_VDATA = b'\xab\xef\xfe\xba'
MAGIC_VEND = b'\xed\xef\xfe\xda'
MAGIC_ERR = b'\xab\xad\xba\xda'

log = logging.getLogger('siphon.ncstream')
log.addHandler(logging.StreamHandler())  # Python 2.7 needs a handler set
log.setLevel(logging.WARNING)


def read_ncstream_messages(fobj):
    messages = []

    while True:
        magic = read_magic(fobj)
        if not magic:
            break

        if magic == MAGIC_HEADER:
            log.debug('Header chunk')
            messages.append(stream.Header())
            messages[0].ParseFromString(read_block(fobj))
            log.debug('Header: %s', str(messages[0]))
        elif magic == MAGIC_DATA:
            log.debug('Data chunk')
            data = stream.Data()
            data.ParseFromString(read_block(fobj))
            log.debug('Data: %s', str(data))
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
                    arr = np.array([np.frombuffer(b, dtype=dt) for b in blocks])
                    messages.append(arr)
                else:
                    messages.append(np.array(blocks, dtype=dt))
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
                arr = reshape_array(data, np.frombuffer(bin_data, dtype=dt))
                messages.append(arr)
            elif data.dataType == stream.STRUCTURE:
                log.debug('Reading structure')
                sd = stream.StructureData()
                sd.ParseFromString(read_block(fobj))
                log.debug('StructureData: %s', str(sd))

                # Make a datatype appropriate to the rows of struct
                endian = '>' if data.bigend else '<'
                dt = np.dtype([(endian, np.void, sd.rowLength)])

                # Turn bytes into an array
                arr = reshape_array(data, np.frombuffer(sd.data, dtype=dt))
                messages.append(arr)
            elif data.dataType == stream.SEQUENCE:
                log.debug('Reading sequence')
                blocks = []
                magic = read_magic(fobj)
                while magic != MAGIC_VEND:
                    if magic == MAGIC_VDATA:
                        log.error('Bad magic for struct/seq data!')
                    blocks.append(stream.StructureData())
                    blocks[0].ParseFromString(read_block(fobj))
                    magic = read_magic(fobj)
                messages.append((data, blocks))
            else:
                raise NotImplementedError("Don't know how to handle data type: {0}".format(
                    data.dataType))
        elif magic == MAGIC_DATA2:
            log.debug('Data2 chunk')
            data = stream.DataCol()
            data.ParseFromString(read_block(fobj))

            log.debug('DataCol:\n%s', str(data))
            arr = datacol_to_array(data)
            messages.append(arr)

        elif magic == MAGIC_ERR:
            err = stream.Error()
            err.ParseFromString(read_block(fobj))
            raise RuntimeError(err.message)
        else:
            log.error('Unknown magic: ' + str(' '.join('%02x' % b for b in magic)))

    return messages


def read_magic(fobj):
    return fobj.read(4)


def read_block(fobj):
    num = read_var_int(fobj)
    log.debug('Next block: %d bytes', num)
    return fobj.read(num)


def process_vlen(data_header, array):
    source = iter(array)
    return np.array([np.fromiter(itertools.islice(source, size), dtype=array.dtype)
                     for size in data_header.vlens])


def datacol_to_array(datacol):
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
    """Extracts the appropriate array shape from the header

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
        if var.dataType is str:
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
    'Read a variable-length integer'
    # Read all bytes from here, stopping with the first one that does not have
    # the MSB set. Save the lower 7 bits, and keep stacking to the *left*.
    val = 0
    shift = 0
    while True:
        # Read next byte
        next_val = ord(file_obj.read(1))
        val = ((next_val & 0x7F) << shift) | val
        shift += 7
        if not next_val & 0x80:
            break

    return val
