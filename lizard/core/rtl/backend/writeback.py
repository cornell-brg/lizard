from pymtl import *
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.messages import ExecuteMsg, WritebackMsg, PipelineMsgStatus
from lizard.util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface
from lizard.core.rtl.kill_unit import PipelineKillDropController
from lizard.core.rtl.controlflow import KillType
from lizard.config.general import *


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

      if s.process_in_.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID:
        s.process_out.rd_val_pair.v = s.process_in_.rd_val_pair
        s.process_out.areg_d.v = s.process_in_.areg_d

        # write the data if the destination is valid
        s.dataflow_write_call.v = s.process_in_.rd_val and s.process_call
        s.dataflow_write_tag.v = s.process_in_.rd
        s.dataflow_write_value.v = s.process_in_.result
      else:
        s.process_out.exception_info.v = s.process_in_.exception_info

  def line_trace(s):
    return s.process_in_.hdr_seq.hex()[2:]


def WritebackDropController():
  return PipelineKillDropController(
      DropControllerInterface(WritebackMsg(), WritebackMsg(),
                              KillType(MAX_SPEC_DEPTH)))


Writeback = gen_stage(WritebackStage, WritebackDropController)
