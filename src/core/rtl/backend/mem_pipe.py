from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from mem.rtl.memory_bus import MemMsgType
from core.rtl.messages import MemFunc, DispatchMsg, ExecuteMsg
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from config.general import *


def MemRequestInterface():
  return StageInterface(DispatchMsg(), DispatchMsg())


class MemRequestStage(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.require(
        MethodSpec(
            'store_pending',
            args={
                'live_mask': Bits(STORE_QUEUE_SIZE),
                'addr': XLEN,
                'size': MEM_SIZE_NBITS,
            },
            rets={
                'pending': Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'send_load',
            args={
                'addr': XLEN,
                'size': MEM_SIZE_NBITS,
            },
            rets=None,
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'enter_store',
            args={
                'id_': STORE_IDX_NBITS,
                'addr': XLEN,
                'size': MEM_SIZE_NBITS,
                'data': XLEN,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'valid_store_mask',
            args=None,
            rets={
                'mask': STORE_QUEUE_SIZE,
            },
            call=False,
            rdy=False,
        ),
    )

    # Address generation
    s.imm = Wire(DECODED_IMM_LEN)
    s.connect(s.imm, s.process_in_.imm)
    s.sext_imm = Wire(XLEN)

    @s.combinational
    def handle_sext_imm():
      s.sext_imm.v = sext(s.imm, XLEN)

    s.addr = Wire(XLEN)
    # The memory message is 8 bytes, so this is 3 bits (numbers 1-8)
    s.len = Wire(MEM_SIZE_NBITS)
    # PYMTL_BROKEN
    s.constant_1 = Wire(MEM_SIZE_NBITS)
    s.connect(s.constant_1, 1)
    s.width = Wire(s.process_in_.mem_msg_width.nbits)
    s.connect(s.width, s.process_in_.mem_msg_width)

    @s.combinational
    def compute_addr():
      s.addr.v = s.process_in_.rs1 + s.sext_imm
      # The width encoding is:
      # 00: Byte (1)
      # 01: Half word (2)
      # 10: Word (4)
      # 11: Double word (8)
      # so 1 << width will compute that
      s.len.v = s.constant_1 << s.width

    s.can_send = Wire(1)
    s.connect(s.store_pending_addr, s.addr)
    s.connect(s.store_pending_size, s.len)
    s.connect(s.store_pending_live_mask, s.valid_store_mask_mask)

    @s.combinational
    def compute_can_send():
      if s.process_in_.mem_msg_func == MemFunc.MEM_FUNC_LOAD:
        s.can_send.v = not s.store_pending_pending and s.send_load_rdy
      else:
        s.can_send.v = 1

    # Accept a request if the memory bus is ready
    s.connect(s.process_accepted, s.can_send)
    # Send a request if we accepted it and are being called
    s.sending_load = Wire(1)
    s.sending_store = Wire(1)

    @s.combinational
    def compute_sending():
      if s.process_in_.mem_msg_func == MemFunc.MEM_FUNC_LOAD:
        s.sending_load.v = s.can_send and s.process_call
        s.sending_store.v = 0
      else:
        s.sending_load.v = 0
        s.sending_store.v = s.can_send and s.process_call

    s.connect(s.send_load_call, s.sending_load)
    s.connect(s.enter_store_call, s.sending_store)
    s.connect(s.send_load_addr, s.addr)
    s.connect(s.send_load_size, s.len)
    s.connect(s.enter_store_id_, s.process_in_.hdr_store_id)
    s.connect(s.enter_store_addr, s.addr)
    s.connect(s.enter_store_size, s.len)
    s.connect(s.enter_store_data, s.process_in_.rs2)

    s.connect(s.process_out, s.process_in_)


def MemResponseInterface():
  return StageInterface(DispatchMsg(), ExecuteMsg())


class MemResponseStage(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'recv_load',
            args=None,
            rets={
                'data': XLEN,
            },
            call=True,
            rdy=True,
        ),)

    s.response_needed = Wire(1)
    s.can_accept = Wire(1)

    @s.combinational
    def compute_accept():
      s.response_needed.v = s.process_in_.mem_msg_func == MemFunc.MEM_FUNC_LOAD
      if s.response_needed:
        s.can_accept.v = s.recv_load_rdy
      else:
        s.can_accept.v = 1

    s.connect(s.process_accepted, s.can_accept)
    s.receiving_load = Wire(1)

    @s.combinational
    def compute_receiving_load():
      s.receiving_load.v = s.can_accept and s.response_needed

    s.connect(s.recv_load_call, s.receiving_load)

    s.result = Wire(XLEN)
    s.data = Wire(XLEN)
    s.connect(s.data, s.recv_load_data)
    s.data_b = Wire(8)
    s.data_h = Wire(16)
    s.data_w = Wire(32)
    s.data_d = Wire(64)
    # PYMTL_BROKEN
    @s.combinational
    def handle_data_slices():
      s.data_b.v = s.data[0:8]
      s.data_h.v = s.data[0:16]
      s.data_w.v = s.data[0:32]
      s.data_d.v = s.data[0:64]

    @s.combinational
    def compute_result():
      if s.process_in_.mem_msg_func == MemFunc.MEM_FUNC_STORE:
        s.result.v = 0
      elif s.process_in_.mem_msg_unsigned:
        if s.process_in_.mem_msg_width == 0:
          s.result.v = zext(s.data_b, XLEN)
        elif s.process_in_.mem_msg_width == 1:
          s.result.v = zext(s.data_h, XLEN)
        else:
          s.result.v = zext(s.data_w, XLEN)
      else:
        if s.process_in_.mem_msg_width == 0:
          s.result.v = sext(s.data_b, XLEN)
        elif s.process_in_.mem_msg_width == 1:
          s.result.v = sext(s.data_h, XLEN)
        elif s.process_in_.mem_msg_width == 2:
          s.result.v = sext(s.data_w, XLEN)
        else:
          s.result.v = sext(s.data_d, XLEN)

    @s.combinational
    def set_process_out():
      s.process_out.v = 0
      s.process_out.hdr.v = s.process_in_.hdr
      s.process_out.result.v = s.result
      s.process_out.rd.v = s.process_in_.rd
      s.process_out.rd_val.v = s.process_in_.rd_val


MemRequest = gen_stage(MemRequestStage)
MemResponse = gen_stage(MemResponseStage)
