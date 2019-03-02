from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManagerInterface
from bitutil import clog2, clog2nz
from util.rtl.register import Register, RegisterInterface
from core.rtl.messages import IssueMsg, DispatchMsg, PipelineMsgStatus
from msg.codes import RVInstMask, Opcode, ExceptionCode


class DispatchInterface(Interface):

  def __init__(s):
    super(DispatchInterface, s).__init__([
        MethodSpec(
            'get',
            args=None,
            rets={
                'msg': DispatchMsg(),
            },
            call=True,
            rdy=True,
        )
    ])


class Dispatch(Model):

  def __init__(s, dispatch_interface):
    UseInterface(s, dispatch_interface)
    preg_nbits = IssueMsg().rs1.nbits
    data_nbits = DispatchMsg().rs1.nbits

    s.require(
        MethodSpec(
            'issue_get',
            args=None,
            rets={'msg': IssueMsg()},
            call=True,
            rdy=True,
        ),
        # Methods needed from dflow:
        MethodSpec(
            'read',
            args={'tag': preg_nbits},
            rets={
                'value': data_nbits,
            },
            call=False,
            rdy=False,
            count=2,
        ),
    )

    s.out_val_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.out_ = Register(RegisterInterface(DispatchMsg(), enable=True))

    s.issued_ = Wire(IssueMsg())
    s.dispatched_ = Wire(DispatchMsg())
    s.accepted_ = Wire(1)

    s.pc_ = Wire(64)
    s.connect(s.pc_, s.issue_get_msg.hdr_pc)

    s.opclass = Wire(3)
    s.connect(s.opclass, s.issue_get_msg.op_class)


    s.connect(s.issued_, s.issue_get_msg)
    s.connect(s.dispatched_, s.out_.write_data)

    s.connect(s.issue_get_call, s.accepted_)
    s.connect(s.out_.write_call, s.accepted_)

    # connect the register file read
    s.connect(s.read_tag[0], s.issue_get_msg.rs1)
    s.connect(s.read_tag[1], s.issue_get_msg.rs2)

    # Connect outgoing method get
    s.connect(s.get_msg, s.out_.read_data)
    s.connect(s.get_rdy, s.out_val_.read_data)

    @s.combinational
    def set_valid():
      s.out_val_.write_data.v = s.accepted_ or (s.out_val_.read_data and
                                                not s.get_call)

    @s.combinational
    def set_accepted():
      s.accepted_.v = (s.get_call or
                       not s.out_val_.read_data) and s.issue_get_rdy

    @s.combinational
    def set_output():
      s.dispatched_.v = 0
      s.dispatched_.hdr.v = s.issued_.hdr
      if s.issued_.hdr_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.dispatched_.exception_info.v = s.issued_.exception_info
        # Copy exception info
        s.dispatched_.exception_info.v = s.issued_.exception_info
      else:
        s.dispatched_.rs1.v = s.read_value[0]
        s.dispatched_.rs1_val.v = s.issued_.rs1_val
        s.dispatched_.rs2.v = s.read_value[1]
        s.dispatched_.rs2_val.v = s.issued_.rs2_val
        s.dispatched_.rd.v = s.issued_.rd
        s.dispatched_.rd_val.v = s.issued_.rd_val
        s.dispatched_.execution_data.v = s.issued_.execution_data
