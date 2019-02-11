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

  def __init__(s, rename_interface, decode_interface, dflow_interface,
               cflow_interface):
    UseInterface(s, rename_interface)

    s.decode = decode_interface
    s.decode.require(s, 'decode', 'get')

    s.dflow = dflow_interface
    s.dflow.require(s, 'dflow', 'get_src', 2)  # We need two ports!
    s.dflow.require(s, 'dflow', 'get_dst')

    s.cflow = cflow_interface
    s.cflow.require(s, 'cflow', 'register')

    s.rdy_ = Wire(1)
    s.accepted_ = Wire(1)
    s.msg_ = Wire(RenameMsg())
    s.decoded_ = Wire(DecodeMsg())

    s.connect(s.decoded_, s.decode_get_msg)
    #s.connect_wire(s.cflow_register_speculative, s.decoded_.speculative)

    s.connect(s.decode_get_call, s.accepted_)

    @s.combinational
    def set_rdy():
      # s.rdy_.v = s.cflow_register_rdy and s.dflow_get_dst_rdy
      s.rdy_.v = s.cflow_register_rdy and s.decode_get_rdy
      s.accepted_.v = s.rdy_ and s.decode_get_rdy
