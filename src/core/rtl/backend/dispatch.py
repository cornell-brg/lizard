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
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from core.rtl.kill_unit import KillDropController


def DispatchInterface():
  return StageInterface(IssueMsg(), DispatchMsg())


class DispatchStage(Model):

  def __init__(s, dispatch_interface):
    UseInterface(s, dispatch_interface)
    preg_nbits = IssueMsg().rs1.nbits
    data_nbits = DispatchMsg().rs1.nbits

    s.require(
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
        ),)

    s.connect(s.process_accepted, 1)
    s.dispatched_ = Wire(DispatchMsg())
    s.connect(s.process_out, s.dispatched_)

    # connect the register file read
    s.connect(s.read_tag[0], s.process_in_.rs1)
    s.connect(s.read_tag[1], s.process_in_.rs2)

    @s.combinational
    def set_output():
      s.dispatched_.v = 0
      s.dispatched_.hdr.v = s.process_in_.hdr
      if s.process_in_.hdr_status != PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.dispatched_.exception_info.v = s.process_in_.exception_info
        # Copy exception info
        s.dispatched_.exception_info.v = s.process_in_.exception_info
      else:
        s.dispatched_.rs1.v = s.read_value[0]
        s.dispatched_.rs1_val.v = s.process_in_.rs1_val
        s.dispatched_.rs2.v = s.read_value[1]
        s.dispatched_.rs2_val.v = s.process_in_.rs2_val
        s.dispatched_.rd.v = s.process_in_.rd
        s.dispatched_.rd_val.v = s.process_in_.rd_val
        s.dispatched_.execution_data.v = s.process_in_.execution_data


def DispatchDropController():
  return KillDropController(DropControllerInterface(DispatchMsg()))


# Dispatch = gen_stage(DispatchStage, DispatchDropController)
Dispatch = gen_stage(DispatchStage)
