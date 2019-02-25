from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.messages import RenameMsg, DecodeMsg
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
    seq_idx_nbits = s.get_msg.seq.nbits
    areg_nbits = DecodeMsg().rs1.nbits
    s.require(
        MethodSpec(
            'decode_get',
            args=None,
            rets={'msg': DecodeMsg()},
            call=True,
            rdy=True,
        ),
        # Methods needed from cflow:
        MethodSpec(
            'register',
            args={'speculative': Bits(1)},
            rets={'seq': Bits(seq_idx_nbits)},
            call=True,
            rdy=True,
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
    s.msg_val_ = RegEnRst(Bits(1))
    s.msg_ = RegEn(RenameMsg())

    s.connect(s.decoded_, s.decode_get_msg)
    s.connect(s.decode_get_call, s.accepted_)

    @s.combinational
    def set_rdy():
      # s.rdy_.v = s.cflow_register_rdy and s.dflow_get_dst_rdy
      s.rdy_.v = s.register_rdy and s.decode_get_rdy
      s.accepted_.v = s.rdy_ and s.decode_get_rdy
