from __future__ import print_function
import zlib

import numpy as np

from . import ncStream_pb2 as stream  # noqa

MAGIC_HEADER = b'\xad\xec\xce\xda'
MAGIC_DATA = b'\xab\xec\xce\xba'
MAGIC_VDATA = b'\xab\xef\xfe\xba'
MAGIC_VEND = b'\xed\xef\xfe\xda'
MAGIC_ERR = b'\xab\xad\xba\xda'


def read_ncstream_messages(fobj):
    messages = []

    while True:
        magic = read_magic(fobj)
        if not magic:
            break

        if magic == MAGIC_HEADER:
            messages.append(stream.Header())
            messages[0].ParseFromString(read_block(fobj))
        elif magic == MAGIC_DATA:
            data = stream.Data()
            data.ParseFromString(read_block(fobj))
            if data.dataType in (stream.STRING, stream.OPAQUE) or data.vdata:
                dt = _dtypeLookup.get(data.dataType, np.object_)
                num_obj = read_var_int(fobj)
                blocks = np.array([read_block(fobj) for _ in range(num_obj)], dtype=dt)
                messages.append(blocks)
            elif data.dataType in _dtypeLookup:
                data_block = read_numpy_block(fobj, data)
                messages.append(data_block)
            elif data.dataType in (stream.STRUCTURE, stream.SEQUENCE):
                blocks = []
                magic = read_magic(fobj)
                while magic != MAGIC_VEND:
                    assert magic == MAGIC_VDATA, 'Bad magic for struct/seq data!'
                    blocks.append(stream.StructureData())
                    blocks[0].ParseFromString(read_block(fobj))
                    magic = read_magic(fobj)
                messages.append((data, blocks))
            else:
                raise NotImplementedError("Don't know how to handle data type: %d" %
                                          data.dataType)
        elif magic == MAGIC_ERR:
            err = stream.Error()
            err.ParseFromString(read_block(fobj))
            raise RuntimeError(err.message)
        else:
            print('Unknown magic: ' + str(' '.join('%02x' % b for b in magic)))

    return messages


def read_magic(fobj):
    return fobj.read(4)


def read_block(fobj):
    num = read_var_int(fobj)
    return fobj.read(num)


def read_numpy_block(fobj, data_header):
    dt = data_type_to_numpy(data_header.dataType)
    dt.newbyteorder('>' if data_header.bigend else '<')
    shape = tuple(r.size for r in data_header.section.range)

    buf = read_block(fobj)
    if data_header.compress == stream.DEFLATE:
        buf = zlib.decompress(buf)
        assert len(buf) == data_header.uncompressedSize
    elif data_header.compress != stream.NONE:
        raise NotImplementedError('Compression type %d not implemented!' %
                                  data_header.compress)

    return np.frombuffer(bytearray(buf), dtype=dt).reshape(*shape)

# STRUCTURE = 8;
# SEQUENCE = 9;
_dtypeLookup = {stream.CHAR: 'b', stream.BYTE: 'b', stream.SHORT: 'i2',
                stream.INT: 'i4', stream.LONG: 'i8', stream.FLOAT: 'f4',
                stream.DOUBLE: 'f8', stream.STRING: np.string_,
                stream.ENUM1: 'B', stream.ENUM2: 'u2', stream.ENUM4: 'u4',
                stream.OPAQUE: 'O'}


def data_type_to_numpy(datatype, unsigned=False):
    basic_type = _dtypeLookup[datatype]

    if datatype in (stream.STRING, stream.OPAQUE):
        return np.dtype(basic_type)

    if unsigned:
        basic_type = basic_type.replace('i', 'u')
    return np.dtype('>' + basic_type)


def unpack_variable(var):
    dt = data_type_to_numpy(var.dataType, var.unsigned)
    if var.dataType == stream.OPAQUE:
        type_name = 'opaque'
    elif var.dataType == stream.STRING:
        type_name = 'string'
    else:
        type_name = dt.type.__name__

    if var.data:
        if var.dataType is str:
            data = var.data
        else:
            data = np.fromstring(var.data, dtype=dt)
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
        print('Warning: Unsigned attribute!')

    if att.len == 0:
        val = None
    elif att.type == stream.Attribute.STRING:
        val = att.sdata
    else:
        val = np.fromstring(att.data,
                            dtype=_attrConverters[att.type], count=att.len)

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
