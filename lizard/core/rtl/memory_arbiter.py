from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.mem.rtl.memory_bus import MemMsgType


class MemoryArbiterInterface(Interface):

  def __init__(s, Addr, Size, Data):
    s.Addr = Addr
    s.Size = Size
    s.Data = Data

    super(MemoryArbiterInterface, s).__init__([
        MethodSpec(
            'recv_load',
            args=None,
            rets={
                'data': s.Data,
            },
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'send_store',
            args={
                'addr': s.Addr,
                'size': s.Size,
                'data': s.Data,
            },
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'send_load',
            args={
                'addr': s.Addr,
                'size': s.Size,
            },
            rets=None,
            call=True,
            rdy=True,
        ),
    ])


class MemoryArbiter(Model):

  def __init__(s, interface, MemMsg):
    UseInterface(s, interface)

    s.require(
        MethodSpec(
            'mb_send',
            args={'msg': MemMsg.req},
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'mb_recv',
            args=None,
            rets={'msg': MemMsg.resp},
            call=True,
            rdy=True,
        ),
    )

    s.store_in_flight = Register(RegisterInterface(Bits(1)))
    s.store_in_flight_after_recv = Wire(1)

    @s.combinational
    def handle_recv():
      s.recv_load_data.v = s.mb_recv_msg.data
      if s.mb_recv_rdy:
        if s.store_in_flight.read_data:
          s.mb_recv_call.v = 1
          s.recv_load_rdy.v = 0
          s.store_in_flight_after_recv.v = 0
        else:
          s.mb_recv_call.v = s.recv_load_call
          s.recv_load_rdy.v = 1
          s.store_in_flight_after_recv.v = 0
      else:
        s.mb_recv_call.v = 0
        s.recv_load_rdy.v = 0
        s.store_in_flight_after_recv.v = s.store_in_flight.read_data

    @s.combinational
    def handle_send_rdy():
      if s.mb_send_rdy:
        s.send_store_rdy.v = 1
        s.send_load_rdy.v = not s.send_store_call
      else:
        s.send_store_rdy.v = 0
        s.send_load_rdy.v = 0

    @s.combinational
    def handle_send(size=s.interface.Size.nbits - 1):
      s.mb_send_msg.v = 0
      if s.send_store_call:
        s.mb_send_call.v = 1
        s.mb_send_msg.type_.v = MemMsgType.WRITE
        s.mb_send_msg.opaque.v = 0
        s.mb_send_msg.addr.v = s.send_store_addr
        # This size will have to be truncated by 1 bit because full for a mem msg
        # is 0. The length field must always be a power of 2 so this works
        s.mb_send_msg.len_.v = s.send_store_size[0:size]
        s.mb_send_msg.data.v = s.send_store_data
        s.store_in_flight.write_data.v = 1
      elif s.send_load_call:
        s.mb_send_call.v = 1
        s.mb_send_msg.type_.v = MemMsgType.READ
        s.mb_send_msg.opaque.v = 0
        s.mb_send_msg.addr.v = s.send_load_addr
        s.mb_send_msg.len_.v = s.send_load_size[0:size]
        s.mb_send_msg.data.v = 0
        s.store_in_flight.write_data.v = 0
      else:
        s.mb_send_call.v = 0
        s.store_in_flight.write_data.v = s.store_in_flight_after_recv
