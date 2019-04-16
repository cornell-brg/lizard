from pymtl import *
from bitutil.bit_struct_generator import *
from config.general import *
from core.rtl.messages import MFunc, MVariant, DispatchMsg, ExecuteMsg
from util.rtl.interface import Interface, UseInterface
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface, PipelineStageInterface
from util.rtl.killable_pipeline_wrapper import InputPipelineAdapterInterface, OutputPipelineAdapterInterface, PipelineWrapper
from core.rtl.kill_unit import PipelineKillDropController
from core.rtl.controlflow import KillType


@bit_struct_generator
def MultIn():
  return [
      Field('a', XLEN),
      Field('b', XLEN),
      Field('func', MFunc.bits),
      Field('variant', MVariant.bits),
      Field('op32', 1),
  ]


def MultOut():
  return Bits(XLEN)


def MultInternalInterface():
  return PipelineStageInterface(MultOut(), None)


class MultInternal(Model):

  def __init__(s, num_stages):
    UseInterface(s, MultInternalInterface())
    # Require the methods of an incoming pipeline stage
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name))
        for m in PipelineStageInterface(MultIn(), None).methods.values()
    ])

    # TODO: AARON
    # You have:
    # in_peek (rdy, msg), where msg is MultIn
    # in_take (call)
    # peek (rdy, msg), where msg is MultOut
    # take (call)
    # DO YOUR THING!


def MultInputPipelineAdapterInterface():
  return InputPipelineAdapterInterface(DispatchMsg(), MultIn(), ExecuteMsg())


class MultInputPipelineAdapter(Model):

  def __init__(s):
    UseInterface(s, MultInputPipelineAdapterInterface())

    s.connect(s.split_internal_in.a, s.split_in_.rs1)
    s.connect(s.split_internal_in.b, s.split_in_.rs2)
    s.connect(s.split_internal_in.func, s.split_in_.m_msg_func)
    s.connect(s.split_internal_in.variant, s.split_in_.m_msg_variant)
    s.connect(s.split_internal_in.op32, s.split_in_.m_msg_op32)

    @s.combinational
    def set_kill_data():
      s.split_kill_data.v = 0
      s.split_kill_data.hdr.v = s.split_in_.hdr
      s.split_kill_data.rd.v = s.split_in_.rd
      s.split_kill_data.rd_val.v = s.split_in_.rd_val


def MultOutputPipelineAdapterInterface():
  return OutputPipelineAdapterInterface(MultOut(), ExecuteMsg(), ExecuteMsg())


class MultOutputPipelineAdapter(Model):

  def __init__(s):
    UseInterface(s, MultOutputPipelineAdapterInterface())

    s.out_temp = Wire(s.interface.Out)
    # PYMTL_BROKEN
    # Use temporary wire to prevent pymtl bug
    @s.combinational
    def compute_out():
      s.out_temp.v = s.fuse_kill_data
      s.out_temp.result.v = s.fuse_internal_out

    s.connect(s.fuse_out, s.out_temp)


def MultDropController():
  return PipelineKillDropController(
      DropControllerInterface(ExecuteMsg(), ExecuteMsg(),
                              KillType(MAX_SPEC_DEPTH)))


def MultInterface():
  return PipelineStageInterface(ExecuteMsg(), KillType(MAX_SPEC_DEPTH))


def Mult():

  def make_internal():
    return MultInternal(MUL_NSTAGES)

  return PipelineWrapper(MultInterface(), MUL_NSTAGES, MultInputPipelineAdapter,
                         make_internal, MultOutputPipelineAdapter,
                         MultDropController)
