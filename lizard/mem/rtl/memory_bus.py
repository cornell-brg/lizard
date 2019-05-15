from pymtl import *
from lizard.util.rtl.interface import Interface
from lizard.util.rtl.method import MethodSpec
from lizard.bitutil import clog2, bit_enum

MemMsgType = bit_enum(
    'MemMsgType',
    None,
    ('READ', 'rd'),
    ('WRITE', 'wr'),
    ('WRITE_INIT', 'in'),
    ('AMO_ADD', 'ad'),
    ('AMO_AND', 'an'),
    ('AMO_OR', 'or'),
    ('AMO_XCHG', 'xg'),
    ('AMO_MIN', 'mn'),
    ('AMO_MAX', 'mx'),
)

MemMsgStatus = bit_enum(
    'MemMsgStatus',
    None,
    ('OK', 'ok'),
    ('ADDRESS_MISALIGNED', 'ma'),
    ('ACCESS_FAULT', 'fa'),
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


class MemReqMsg(BitStructDefinition):

  def __init__(s, opaque_nbits, addr_nbits, data_nbytes):
    s.opaque_nbits = opaque_nbits
    s.addr_nbits = addr_nbits
    s.data_nbytes = data_nbytes
    s.len_nbits = clog2(data_nbytes)

    s.type_ = BitField(MemMsgType.bits)
    s.opaque = BitField(opaque_nbits)
    s.addr = BitField(addr_nbits)
    s.len_ = BitField(s.len_nbits)
    s.data = BitField(data_nbytes * 8)

  def mk_rd(s, opaque, addr, len_):
    msg = s()
    msg.type_ = MemMsgType.READ
    msg.opaque = opaque
    msg.addr = addr
    msg.len_ = len_
    msg.data = 0

    return msg

  def mk_wr(s, opaque, addr, len_, data):
    msg = s()
    msg.type_ = MemMsgType.WRITE
    msg.opaque = opaque
    msg.addr = addr
    msg.len_ = len_
    msg.data = data

    return msg

  def mk_msg(s, type_, opaque, addr, len_, data):
    msg = s()
    msg.type_ = type_
    msg.opaque = opaque
    msg.addr = addr
    msg.len_ = len_
    msg.data = data

    return msg

  def __str__(s):
    return "{}:{}:{}:{}".format(
        MemMsgType.short(s.type_), s.opaque, s.addr, s.data)


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


class MemRespMsg(BitStructDefinition):

  def __init__(s, opaque_nbits, test_nbits, data_nbytes):
    s.opaque_nbits = opaque_nbits
    s.test_nbits = test_nbits
    s.data_nbytes = data_nbytes

    s.type_ = BitField(MemMsgType.bits)
    s.opaque = BitField(opaque_nbits)
    s.test = BitField(test_nbits)
    s.stat = BitField(MemMsgStatus.bits)
    s.len_ = BitField(clog2(data_nbytes))
    s.data = BitField(data_nbytes * 8)

  def mk_rd(s, opaque, len_, data):
    msg = s()
    msg.type_ = MemMsgType.READ
    msg.opaque = opaque
    msg.test = 0
    msg.stat = 0
    msg.len_ = len_
    msg.data = data

    return msg

  def mk_wr(s, opaque, len_):
    msg = s()
    msg.type_ = MemMsgType.WRITE
    msg.opaque = opaque
    msg.test = 0
    msg.stat = 0
    msg.len_ = len_
    msg.data = 0

    return msg

  def mk_msg(s, type_, opaque, stat, len_, data):
    msg = s()
    msg.type_ = type_
    msg.opaque = opaque
    msg.test = 0
    msg.stat = stat
    msg.len_ = len_
    msg.data = data

    return msg

  def __str__(s):
    return "{}:{}:{}:{}:{}".format(
        MemMsgType.short(s.type_), s.opaque, s.test, s.stat, s.data)


class MemMsg(object):

  def __init__(s, opaque_nbits, test_nbits, addr_nbits, data_nbytes):
    s.opaque_nbits = opaque_nbits
    s.test_nbits = test_nbits
    s.addr_nbits = addr_nbits
    s.data_nbytes = data_nbytes

    s.req = MemReqMsg(opaque_nbits, addr_nbits, data_nbytes)
    s.resp = MemRespMsg(opaque_nbits, test_nbits, data_nbytes)

  def __str__(s):
    return 'MemMsg: op: {} ts: {} ad: {} da: {}'.format(s.opaque_nbits,
                                                        s.test_nbits,
                                                        s.addr_nbits,
                                                        s.data_nbytes)


class MemoryBusInterface(Interface):

  def __init__(s, num_ports, opaque_nbits, test_nbits, addr_nbits, data_nbytes):
    s.num_ports = num_ports
    s.opaque_nbits = opaque_nbits
    s.test_nbits = test_nbits
    s.addr_nbits = addr_nbits
    s.data_nbytes = data_nbytes

    s.MemMsg = MemMsg(opaque_nbits, test_nbits, addr_nbits, data_nbytes)

    methods = []
    for i in range(num_ports):
      methods.extend([
          MethodSpec(
              'cl_delay_{}'.format(i),
              args=None,
              rets=None,
              call=False,
              rdy=False,
          ),
          MethodSpec(
              'recv_{}'.format(i),
              args=None,
              rets={'msg': s.MemMsg.resp},
              call=True,
              rdy=True,
          ),
          MethodSpec(
              'send_{}'.format(i),
              args={'msg': s.MemMsg.req},
              rets=None,
              call=True,
              rdy=True,
          ),
      ])
    super(MemoryBusInterface, s).__init__(methods)
