from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from bitutil import clog2, clog2nz

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


class MemoryBusInterface(Interface):

  def __init__(s, num_ports, opaque_nbits, test_nbits, addr_nbits, data_nbytes):
    s.num_ports = num_ports
    s.opaque_nbits = opaque_nbits
    s.test_nbits = test_nbits
    s.addr_nbits = addr_nbits
    s.data_nbytes = data_nbytes

    super(MemoryBusInterface, s).__init__([
        MethodSpec(
            'recv',
            args=None,
            rets={
                'type_': Bits(MemMsgType.bits),
                'opaque': Bits(opaque_nbits),
                'test': Bits(test_nbits),
                'stat': Bits(MemMsgStatus.bits),
                'len': Bits(clog2(data_nbytes)),
                'data': Bits(data_nbytes * 8),
            },
            call=True,
            rdy=True,
            count=num_ports,
        ),
        MethodSpec(
            'send',
            args={
                'type_': Bits(MemMsgType.bits),
                'opaque': Bits(opaque_nbits),
                'addr': Bits(addr_nbits),
                'len': Bits(clog2(data_nbytes)),
                'data': Bits(data_nbytes * 8),
            },
            rets=None,
            call=True,
            rdy=True,
            count=num_ports,
        ),
    ])
