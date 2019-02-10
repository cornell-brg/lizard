from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.messages import RenameMsg
from msg.codes import RVInstMask, Opcode, ExceptionCode
from core.rtl.frontend.decode import DecodeInterface


class RenameInterface(Interface):

  def __init__(s):
    super(RenameInterface, s).__init__(
        [],
        ordering_chains=[
            [],
        ],
    )


class Rename(Model):

  def __init__(s, xlen, seq_idx_nbits, areg_count, areg_tag_nbits, preg_count,
               max_spec_depth, nsrc_ports, ndst_ports):
    UseInterface(s, RenameInterface())

    s.decode = DecodeInterface()
    s.decode.require(s, 'decode', 'get')

    s.dflow = DataFlowManagerInterface(xlen, areg_count, preg_count,
                                       max_spec_depth, nsrc_ports, ndst_ports)
    s.dflow.require(s, 'dflow', 'get_src', 2) # We need two ports!
    s.dflow.require(s, 'dflow', 'get_dst')

    s.cflow = ControlFlowManagerInterface(xlen, seq_idx_nbits)
    s.cflow.require(s, 'cflow', 'register')

    s.rdy_ = Wire(1)
    s.msg_ = Wire(RenameMsg())

    s.connect(s.cflow_register_speculative, s.decode_get_msg.speculative)
    s.connect(s.decode_get_call, s.rdy_)

    @s.combinational
    def set_rdy():
      # s.rdy_.v = s.cflow_register_rdy and s.dflow_get_dst_rdy
      s.rdy_.v = s.cflow_register_rdy and s.decode_get_rdy
