from pymtl import *

from bitutil import clog2, bit_enum
from config.mem import *
from config.general import *

MemMsgType = bit_enum(
    'MemMsgType',
    None,
    ( 'READ', 'rd' ),
    ( 'WRITE', 'wr' ),
    ( 'WRITE_INIT', 'in' ),
    ( 'AMO_ADD', 'ad' ),
    ( 'AMO_AND', 'an' ),
    ( 'AMO_OR', 'or' ),
    ( 'AMO_XCHG', 'xg' ),
    ( 'AMO_MIN', 'mn' ),
    ( 'AMO_MAX', 'mx' ),
)

MemMsgStatus = bit_enum(
    'MemMsgStatus',
    None,
    ( 'OK', 'ok' ),
    ( 'ADDRESS_MISALIGNED', 'ma' ),
    ( 'ACCESS_FAULT', 'fa' ),
)

#-------------------------------------------------------------------------
# MemReqMsg
#-------------------------------------------------------------------------
# Memory request messages can be of various types. The most basic are for
# a read or write, although there is encoding space for more message
# types such as atomic memory operations and prefetch requests. Read
# requests include an address and the number of bytes to read, while
# write requests include an address, the number of bytes to write, and
# the actual data to write. Both kinds of messages include an opaque
# field, which must be preserved in the response.
#
# Message Format:
#
#          opaque  addr               data
#    3b    nbits   nbits       calc   nbits
#  +------+------+-----------+------+-----------+
#  | type |opaque| addr      | len  | data      |
#  +------+------+-----------+------+-----------+
#
# The size of the length field is caclulated from the number of bits in
# the data field, and is expressed in _bytes_. If the value of the length
# field is zero, then the read or write should be for the full width of the
# data field.


class MemReqMsg( BitStructDefinition ):

  def __init__( s, opaque_nbits, addr_nbits, data_nbits ):
    s.type_ = BitField( MemMsgType.bits )
    s.opaque = BitField( opaque_nbits )
    s.addr = BitField( addr_nbits )
    s.len = BitField( clog2( data_nbits / 8 ) )
    s.data = BitField( data_nbits )

  def mk_rd( s, opaque, addr, len_ ):
    msg = s()
    msg.type_ = MemMsgType.READ
    msg.opaque = opaque
    msg.addr = addr
    msg.len = len_
    msg.data = 0

    return msg

  def mk_wr( s, opaque, addr, len_, data ):
    msg = s()
    msg.type_ = MemMsgType.WRITE
    msg.opaque = opaque
    msg.addr = addr
    msg.len = len_
    msg.data = data

    return msg

  def mk_msg( s, type_, opaque, addr, len_, data ):
    msg = s()
    msg.type_ = type_
    msg.opaque = opaque
    msg.addr = addr
    msg.len = len_
    msg.data = data

    return msg

  def __str__( s ):
    return "{}:{}:{}:{}".format(
        MemMsgType.short( s.type_ ), s.opaque, s.addr, s.data )


#-------------------------------------------------------------------------
# MemRespMsg
#-------------------------------------------------------------------------
# Memory response messages can be of various types. The most basic are
# for a read or write, although there is encoding space for more message
# types such as atomic memory operations and prefetch responses. Read
# responses include the actual data and the number of bytes, while write
# responses currently include just the type. Both kinds of messages
# include an opaque field and corresponding opaque field valid bit, as
# well as a two-bit test field.
#
# Message Format:
#
#          opaque                       data
#    3b    nbits   2b     2b     calc   nbits
#  +------+------+------+------+------+-----------+
#  | type |opaque| test | stat | len  | data      |
#  +------+------+------+------+------+-----------+
#
# The size of the length field is caclulated from the number of bits in
# the data field, and is expressed in _bytes_. If the value of the length
# field is zero, then the read or write should be for the full width of the
# data field.
#
# The test field is reserved for use by memory models for testing. For
# example, a cache model could use a test bit to indicate if a memory
# request is a cache hit or miss for testing purposes.


class MemRespMsg( BitStructDefinition ):

  def __init__( s, opaque_nbits, data_nbits ):
    s.type_ = BitField( MemMsgType.bits )
    s.opaque = BitField( opaque_nbits )
    s.test = BitField( 2 )
    s.stat = BitField( MemMsgStatus.bits )
    s.len = BitField( clog2( data_nbits / 8 ) )
    s.data = BitField( data_nbits )

  def mk_rd( s, opaque, len_, data ):
    msg = s()
    msg.type_ = MemMsgType.READ
    msg.opaque = opaque
    msg.test = 0
    msg.stat = 0  # stat
    msg.len = len_
    msg.data = data

    return msg

  def mk_wr( s, opaque, stat, len_ ):
    msg = s()
    msg.type_ = MemMsgType.WRITE
    msg.opaque = opaque
    msg.test = 0
    msg.stat = stat
    msg.len = len_
    msg.data = 0

    return msg

  def mk_msg( s, type_, opaque, stat, len_, data ):
    msg = s()
    msg.type_ = type_
    msg.opaque = opaque
    msg.test = 0
    msg.stat = stat
    msg.len = len_
    msg.data = data

    return msg

  def __str__( s ):
    return "{}:{}:{}:{}".format(
        MemMsgType.short( s.type_ ), s.test, s.stat, s.data )


#-------------------------------------------------------------------------
# MemMsg
#-------------------------------------------------------------------------
# Single class that contains both the memory request and response types.
# This simplifies parameterizing models both both message types since (1)
# we can specifcy the opaque, address, and data nbits in a single step,
# and (2) we can pass a single object into the parameterized model.


class MemMsg( object ):

  def __init__( s, opaque_nbits, addr_nbits, data_nbits ):
    s.req = MemReqMsg( opaque_nbits, addr_nbits, data_nbits )
    s.resp = MemRespMsg( opaque_nbits, data_nbits )


MemMsg4B = MemMsg( OPAQUE_SIZE, XLEN, 32 )
MemMsg8B = MemMsg( OPAQUE_SIZE, XLEN, 64 )
MemMsg16B = MemMsg( OPAQUE_SIZE, XLEN, 128 )
