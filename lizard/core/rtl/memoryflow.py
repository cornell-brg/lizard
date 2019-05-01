from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type
from lizard.util.rtl.registerfile import RegisterFile
from lizard.util.rtl.overlap_checker import OverlapChecker, OverlapCheckerInterface
from lizard.util.rtl.logic import LogicOperatorInterface, Or
from lizard.core.rtl.memory_arbiter import MemoryArbiterInterface, MemoryArbiter
from lizard.bitutil import clog2, clog2nz
from lizard.bitutil.bit_struct_generator import *


class MemoryFlowManagerInterface(Interface):

  def __init__(s, addr_len, max_size, nslots):
    s.nslots = nslots
    s.max_size = max_size
    s.StoreID = canonicalize_type(clog2nz(nslots))
    s.Addr = canonicalize_type(addr_len)
    s.Size = canonicalize_type(clog2nz(max_size + 1))
    # size is in bytes
    s.Data = Bits(max_size * 8)

    super(MemoryFlowManagerInterface, s).__init__([
        MethodSpec(
            'store_pending',
            args={
                'live_mask': Bits(nslots),
                'addr': s.Addr,
                'size': s.Size,
            },
            rets={
                'pending': Bits(1),
            },
            call=False,
            rdy=False,
        ),
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
            'store_data_available',
            args={
                'id_': s.StoreID,
            },
            rets={
                'ret': Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'send_store',
            args={
                'id_': s.StoreID,
            },
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'store_acks_outstanding',
            args=None,
            rets={
                'ret': Bits(1),
            },
            call=False,
            rdy=False,
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
        MethodSpec(
            'register_store',
            args={
                'id_': s.StoreID,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'enter_store_address',
            args={
                'id_': s.StoreID,
                'addr': s.Addr,
                'size': s.Size,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'enter_store_data',
            args={
                'id_': s.StoreID,
                'data': s.Data,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    ])


@bit_struct_generator
def AddrSizePair(addr_len, size_len):
  return [
      Field('addr', addr_len),
      Field('size', size_len),
  ]


class MemoryFlowManager(Model):

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

    s.store_address_table = RegisterFile(
        AddrSizePair(s.interface.Addr.nbits, s.interface.Size.nbits),
        s.interface.nslots, 1, 1, False, False)
    s.address_valid_table = RegisterFile(
        Bits(1), s.interface.nslots, 0, 2, False, False,
        [0] * s.interface.nslots)
    s.store_data_table = RegisterFile(s.interface.Data, s.interface.nslots, 1,
                                      1, False, False)
    s.data_valid_table = RegisterFile(
        Bits(1), s.interface.nslots, 1, 2, False, False,
        [0] * s.interface.nslots)
    s.overlap_checkers = [
        OverlapChecker(
            OverlapCheckerInterface(s.interface.Addr.nbits,
                                    s.interface.max_size))
        for _ in range(s.interface.nslots)
    ]
    s.memory_arbiter = MemoryArbiter(
        MemoryArbiterInterface(s.interface.Addr, s.interface.Size,
                               s.interface.Data), MemMsg)
    s.connect_m(s.memory_arbiter.mb_send, s.mb_send)
    s.connect_m(s.memory_arbiter.mb_recv, s.mb_recv)
    s.connect_m(s.memory_arbiter.store_acks_outstanding,
                s.store_acks_outstanding)

    s.overlapped_and_live = [Wire(1) for _ in range(s.interface.nslots)]
    # PYMTL_BROKEN for some reason reduce_or verilates, but then the C++ fails to compile
    s.or_ = Or(LogicOperatorInterface(s.interface.nslots))
    for i in range(s.interface.nslots):
      s.connect(s.overlap_checkers[i].check_base_a, s.store_pending_addr)
      s.connect(s.overlap_checkers[i].check_size_a, s.store_pending_size)
      s.connect(s.overlap_checkers[i].check_base_b,
                s.store_address_table.dump_out[i].addr)
      s.connect(s.overlap_checkers[i].check_size_b,
                s.store_address_table.dump_out[i].size)

      s.connect(s.or_.op_in_[i], s.overlapped_and_live[i])

      @s.combinational
      def check_overlapped(i=i):
        s.overlapped_and_live[i].v = not s.overlap_checkers[
            i].check_disjoint and s.store_pending_live_mask[
                i] and s.address_valid_table.dump_out[i]

    s.connect(s.store_pending_pending, s.or_.op_out)

    s.connect(s.address_valid_table.write_call[0], s.register_store_call)
    s.connect(s.address_valid_table.write_addr[0], s.register_store_id_)
    s.connect(s.address_valid_table.write_data[0], 0)
    s.connect(s.data_valid_table.write_call[0], s.register_store_call)
    s.connect(s.data_valid_table.write_addr[0], s.register_store_id_)
    s.connect(s.data_valid_table.write_data[0], 0)

    s.connect(s.store_address_table.write_call[0], s.enter_store_address_call)
    s.connect(s.store_address_table.write_addr[0], s.enter_store_address_id_)
    s.connect(s.store_address_table.write_data[0].addr,
              s.enter_store_address_addr)
    s.connect(s.store_address_table.write_data[0].size,
              s.enter_store_address_size)
    s.connect(s.address_valid_table.write_call[1], s.enter_store_address_call)
    s.connect(s.address_valid_table.write_addr[1], s.enter_store_address_id_)
    s.connect(s.address_valid_table.write_data[1], 1)

    s.connect(s.store_data_table.write_call[0], s.enter_store_data_call)
    s.connect(s.store_data_table.write_addr[0], s.enter_store_data_id_)
    s.connect(s.store_data_table.write_data[0], s.enter_store_data_data)
    s.connect(s.data_valid_table.write_call[1], s.enter_store_data_call)
    s.connect(s.data_valid_table.write_addr[1], s.enter_store_data_id_)
    s.connect(s.data_valid_table.write_data[1], 1)

    s.connect_m(s.memory_arbiter.recv_load, s.recv_load)
    s.connect_m(s.memory_arbiter.send_load, s.send_load)
    s.connect(s.store_address_table.read_addr[0], s.send_store_id_)
    s.connect(s.store_data_table.read_addr[0], s.send_store_id_)
    s.connect(s.memory_arbiter.send_store_addr,
              s.store_address_table.read_data[0].addr)
    s.connect(s.memory_arbiter.send_store_size,
              s.store_address_table.read_data[0].size)
    s.connect(s.memory_arbiter.send_store_data, s.store_data_table.read_data[0])
    s.connect(s.memory_arbiter.send_store_call, s.send_store_call)
    s.connect(s.send_store_rdy, s.memory_arbiter.send_store_rdy)

    s.connect(s.data_valid_table.read_addr[0], s.store_data_available_id_)
    s.connect(s.store_data_available_ret, s.data_valid_table.read_data[0])

    s.connect(s.store_address_table.set_call, 0)
    for port in s.store_address_table.set_in_:
      s.connect(port, 0)
    s.connect(s.address_valid_table.set_call, 0)
    for port in s.address_valid_table.set_in_:
      s.connect(port, 0)
    s.connect(s.store_data_table.set_call, 0)
    for port in s.store_data_table.set_in_:
      s.connect(port, 0)
    s.connect(s.data_valid_table.set_call, 0)
    for port in s.data_valid_table.set_in_:
      s.connect(port, 0)
