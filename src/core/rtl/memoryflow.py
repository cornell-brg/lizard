from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type
from util.rtl.registerfile import RegisterFile
from util.rtl.overlap_checker import OverlapChecker, OverlapCheckerInterface
from util.rtl.logic import LogicOperatorInterface, Or
from core.rtl.memory_arbiter import MemoryArbiterInterface, MemoryArbiter
from bitutil import clog2, clog2nz
from bitutil.bit_struct_generator import *


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
            'send_store',
            args={
                'id_': s.StoreID,
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
            'enter_store',
            args={
                'id_': s.StoreID,
                'addr': s.Addr,
                'size': s.Size,
                'data': s.Data,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    ])


@bit_struct_generator
def StoreSpec(addr_len, size_len, data_len):
  return [
      Field('addr', addr_len),
      Field('size', size_len),
      Field('data', data_len),
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

    s.store_table = RegisterFile(
        StoreSpec(s.interface.Addr.nbits, s.interface.Size.nbits,
                  s.interface.Data.nbits), s.interface.nslots, 1, 1, False,
        False)
    s.valid_table = RegisterFile(
        Bits(1), s.interface.nslots, 0, 2, False, False,
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

    s.overlapped_and_live = [Wire(1) for _ in range(s.interface.nslots)]
    # PYMTL_BROKEN for some reason reduce_or verilates, but then the C++ fails to compile
    s.or_ = Or(LogicOperatorInterface(s.interface.nslots))
    for i in range(s.interface.nslots):
      s.connect(s.overlap_checkers[i].check_base_a, s.store_pending_addr)
      s.connect(s.overlap_checkers[i].check_size_a, s.store_pending_size)
      s.connect(s.overlap_checkers[i].check_base_b,
                s.store_table.dump_out[i].addr)
      s.connect(s.overlap_checkers[i].check_size_b,
                s.store_table.dump_out[i].size)

      s.connect(s.or_.op_in_[i], s.overlapped_and_live[i])

      @s.combinational
      def check_overlapped(i=i):
        s.overlapped_and_live[i].v = not s.overlap_checkers[
            i].check_disjoint and s.store_pending_live_mask[
                i] and s.valid_table.dump_out[i]

    s.connect(s.store_pending_pending, s.or_.op_out)

    s.connect(s.valid_table.write_call[0], s.register_store_call)
    s.connect(s.valid_table.write_addr[0], s.register_store_id_)
    s.connect(s.valid_table.write_data[0], 0)

    s.connect(s.store_table.write_call[0], s.enter_store_call)
    s.connect(s.store_table.write_addr[0], s.enter_store_id_)
    s.connect(s.store_table.write_data[0].addr, s.enter_store_addr)
    s.connect(s.store_table.write_data[0].size, s.enter_store_size)
    s.connect(s.store_table.write_data[0].data, s.enter_store_data)
    s.connect(s.valid_table.write_call[1], s.enter_store_call)
    s.connect(s.valid_table.write_addr[1], s.enter_store_id_)
    s.connect(s.valid_table.write_data[1], 1)

    s.connect_m(s.memory_arbiter.recv_load, s.recv_load)
    s.connect_m(s.memory_arbiter.send_load, s.send_load)
    s.connect(s.store_table.read_addr[0], s.send_store_id_)
    s.connect(s.memory_arbiter.send_store_addr, s.store_table.read_data[0].addr)
    s.connect(s.memory_arbiter.send_store_size, s.store_table.read_data[0].size)
    s.connect(s.memory_arbiter.send_store_data, s.store_table.read_data[0].data)
    s.connect(s.memory_arbiter.send_store_call, s.send_store_call)
    s.connect(s.send_store_rdy, s.memory_arbiter.send_store_rdy)

    s.connect(s.store_table.set_call, 0)
    for port in s.store_table.set_in_:
      s.connect(port, 0)
    s.connect(s.valid_table.set_call, 0)
    for port in s.valid_table.set_in_:
      s.connect(port, 0)
