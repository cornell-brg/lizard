from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.register import Register, RegisterInterface
from core.rtl.messages import ExecuteMsg, WritebackMsg, PipelineMsgStatus
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from core.rtl.kill_unit import PipelineKillDropController
from core.rtl.controlflow import KillType
from config.general import *


def WritebackInterface():
  return StageInterface(ExecuteMsg(), WritebackMsg())


class WritebackStage(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'dataflow_write',
            args={
                'tag': PREG_IDX_NBITS,
                'value': XLEN,
            },
            rets=None,
            call=True,
            rdy=False,
        ),)

    s.connect(s.process_accepted, 1)
    s.is_store_DEBUG = Wire(1)
    s.connect(s.is_store_DEBUG, s.process_in_.hdr_is_store)

    @s.combinational
    def compute():
      s.process_out.v = 0
      s.process_out.hdr.v = s.process_in_.hdr

      s.dataflow_write_call.v = 0
      s.dataflow_write_tag.v = 0
      s.dataflow_write_value.v = 0

      if s.process_call:
        if s.process_in_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
          s.process_out.rd_val_pair.v = s.process_in_.rd_val_pair

          # write the data if the destination is valid
          s.dataflow_write_call.v = s.process_in_.rd_val
          s.dataflow_write_tag.v = s.process_in_.rd
          s.dataflow_write_value.v = s.process_in_.result
        else:
          s.process_out.exception_info.v = s.process_in_.exception_info


def WritebackDropController():
  return PipelineKillDropController(
      DropControllerInterface(WritebackMsg(), WritebackMsg(),
                              KillType(MAX_SPEC_DEPTH)))


Writeback = gen_stage(WritebackStage, WritebackDropController)
