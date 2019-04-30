from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.messages import MemFunc, DispatchMsg, ExecuteMsg
from lizard.util.rtl.pipeline_stage import gen_stage, StageInterface, PipelineStageInterface
from lizard.util.rtl.killable_pipeline_wrapper import InputPipelineAdapterInterface, OutputPipelineAdapterInterface, PipelineWrapper
from lizard.util import line_block
from lizard.util.line_block import Divider
from lizard.core.rtl.controlflow import KillType
from lizard.core.rtl.kill_unit import KillDropController, KillDropControllerInterface
from lizard.config.general import *


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
    s.DEBUG_PC = Wire(XLEN)
    s.connect(s.DEBUG_PC, s.process_in_.hdr_pc)

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

  def line_trace(s):
    return s.process_in_.hdr_seq.hex()[2:]


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
        ))

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
      s.receiving_load.v = s.process_call and s.response_needed

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
      s.process_out.areg_d.v = s.process_in_.areg_d

  def line_trace(s):
    return s.process_in_.hdr_seq.hex()[2:]


MemRequest = gen_stage(MemRequestStage)
MemResponse = gen_stage(MemResponseStage)


def MemJointInterface():
  return PipelineStageInterface(ExecuteMsg(), None)


class MemJoint(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.mem_request = MemRequest(MemRequestInterface())
    s.mem_response = MemResponse(MemResponseInterface())
    s.require(
        MethodSpec(
            'recv_load',
            args=None,
            rets={
                'data': XLEN,
            },
            call=True,
            rdy=True,
        ),
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
    s.connect_m(s.mem_request.store_pending, s.store_pending)
    s.connect_m(s.mem_request.send_load, s.send_load)
    s.connect_m(s.mem_request.enter_store, s.enter_store)
    s.connect_m(s.mem_request.valid_store_mask, s.valid_store_mask)
    s.connect_m(s.mem_response.recv_load, s.recv_load)

    # Require the methods of an incoming pipeline stage
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name))
        for m in PipelineStageInterface(DispatchMsg(), None).methods.values()
    ])

    s.connect_m(s.mem_request.in_peek, s.in_peek)
    s.connect_m(s.mem_request.in_take, s.in_take)
    s.connect_m(s.mem_response.in_peek, s.mem_request.peek)
    s.connect_m(s.mem_response.in_take, s.mem_request.take)
    s.connect_m(s.peek, s.mem_response.peek)
    s.connect_m(s.take, s.mem_response.take)

  def line_trace(s):
    return line_block.join([
        s.mem_request.line_trace(),
        Divider(' | '),
        s.mem_response.line_trace()
    ])


def BranchMaskInputPipelineAdapterInterface(In):
  return InputPipelineAdapterInterface(In, In, Bits(In.hdr_branch_mask.nbits))


class BranchMaskInputPipelineAdapter(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.connect(s.split_internal_in, s.split_in_)
    s.connect(s.split_kill_data, s.split_in_.hdr_branch_mask)


def BranchMaskOutputPipelineAdapterInterface(Out):
  return OutputPipelineAdapterInterface(Out, Bits(Out.hdr_branch_mask.nbits),
                                        Out)


class BranchMaskOutputPipelineAdapter(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.out_temp = Wire(s.interface.Out)
    # PYMTL_BROKEN
    # Use temporary wire to prevent pymtl bug
    @s.combinational
    def compute_out():
      s.out_temp.v = s.fuse_internal_out
      s.out_temp.hdr_branch_mask.v = s.fuse_kill_data

    s.connect(s.fuse_out, s.out_temp)


def MemInputPipelineAdapter():
  return BranchMaskInputPipelineAdapter(
      BranchMaskInputPipelineAdapterInterface(DispatchMsg()))


def MemOutputPipelineAdapter():
  return BranchMaskOutputPipelineAdapter(
      BranchMaskOutputPipelineAdapterInterface(ExecuteMsg()))


def MemDropController():
  return KillDropController(KillDropControllerInterface(MAX_SPEC_DEPTH))


def MemInterface():
  return PipelineStageInterface(ExecuteMsg(), KillType(MAX_SPEC_DEPTH))


def Mem(interface):

  def internal_pipeline():
    return MemJoint(MemJointInterface())

  return PipelineWrapper(interface, 2, MemInputPipelineAdapter,
                         internal_pipeline, MemOutputPipelineAdapter,
                         MemDropController)
