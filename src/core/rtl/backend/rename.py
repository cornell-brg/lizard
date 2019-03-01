from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManagerInterface
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface
from core.rtl.messages import RenameMsg, DecodeMsg, PipelineMsgStatus
from msg.codes import RVInstMask, Opcode, ExceptionCode
from core.rtl.frontend.decode import DecodeInterface


class RenameInterface(Interface):

  def __init__(s):
    super(RenameInterface, s).__init__([
        MethodSpec(
            'get',
            args=None,
            rets={
                'msg': RenameMsg(),
            },
            call=True,
            rdy=True,
        )
    ])


class Rename(Model):

  def __init__(s, rename_interface):
    UseInterface(s, rename_interface)
    preg_nbits = s.get_msg.rs1.nbits
    seq_idx_nbits = s.get_msg.hdr_seq.nbits
    pc_nbits = DecodeMsg().hdr_pc.nbits
    areg_nbits = DecodeMsg().rs1.nbits
    s.require(
        MethodSpec(
            'decode_peek',
            args=None,
            rets={'msg': DecodeMsg()},
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'decode_take',
            call=True,
            rdy=False,
        ),
        # Methods needed from cflow:
        MethodSpec(
            'register',
            args={
                'speculative': Bits(1),
                'pc': Bits(pc_nbits),
                'pc_succ': Bits(pc_nbits),
            },
            rets={
                'seq': Bits(seq_idx_nbits),
                'success' : Bits(1),
            },
            call=True,
            rdy=False,
        ),
        # Methods from dataflow
        MethodSpec(
            'get_src',
            args={'areg': areg_nbits},
            rets={'preg': preg_nbits},
            call=False,
            rdy=False,
            count=2,
        ),
        MethodSpec(
            'get_dst',
            args={'areg': areg_nbits},
            rets={'preg': preg_nbits},
            call=True,
            rdy=True,
        ),
    )
    s.rdy_ = Wire(1)
    s.accepted_ = Wire(1)

    s.decoded_ = Wire(DecodeMsg())

    # Outgoing pipeline reigster
    s.msg_val_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.msg_ = Register(RegisterInterface(RenameMsg(), enable=True))
    s.out_ = Wire(RenameMsg())

    # Connect up get call
    s.connect(s.get_rdy, s.msg_val_.read_data)
    s.connect(s.get_msg, s.msg_.read_data)

    s.connect(s.decoded_, s.decode_peek_msg)
    s.connect(s.msg_.write_data, s.out_)

    # Outgoing call's arguments
    s.connect(s.register_speculative, s.decoded_.speculative)
    s.connect(s.register_pc, s.decoded_.hdr_pc)
    s.connect(s.register_pc_succ, s.decoded_.pc_succ)
    s.connect(s.get_src_areg[0], s.decoded_.rs1)
    s.connect(s.get_src_areg[1], s.decoded_.rs2)
    s.connect(s.get_dst_areg, s.decoded_.rd)

    # Outgoing call's call signal:
    s.connect(s.decode_take_call, s.accepted_)
    s.connect(s.register_call, s.rdy_)
    s.connect(s.msg_.write_call, s.accepted_)
    # Handle the conditional calls
    @s.combinational
    def handle_calls():
      s.get_dst_call.v = s.decoded_.rd_val and (
          s.decoded_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID)

    # Connect the outgoing signals
    @s.combinational
    def handle_out():
      s.out_.v = 0  # No inferred latches
      s.out_.hdr_frontend_hdr.v = s.decoded_.hdr
      s.out_.hdr_seq.v = s.register_seq
      s.out_.hdr_branch_mask.v = 0  # TODO set this properly with cflow
      # We need to propogate exception info
      if s.decoded_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.out_.rs1_val.v = s.decoded_.rs1_val
        s.out_.rs2_val.v = s.decoded_.rs2_val
        s.out_.rd_val.v = s.decoded_.rd_val
        # Copy over the aregs
        s.out_.rs1.v = s.get_src_preg[0]
        s.out_.rs2.v = s.get_src_preg[1]
        s.out_.rd.v = s.get_dst_preg
        # Copy the execution stuff
        s.out_.execution_data.v = s.decoded_.execution_data
      else:
        s.out_.exception_info.v = s.decoded_.exception_info

    # Set the valid register
    @s.combinational
    def set_val():
      s.msg_val_.write_data.v = s.accepted_ or (s.msg_val_.read_data and
                                                not s.get_call)

    @s.combinational
    def set_rdy():
      s.rdy_.v = s.get_dst_rdy and s.decode_peek_rdy and (
                                          not s.msg_val_.read_data or s.get_call)
      s.accepted_.v = s.rdy_ and s.register_success
