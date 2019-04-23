from pymtl import *
from lizard.bitutil.bit_struct_generator import *
from lizard.config.general import *
from lizard.core.rtl.messages import MFunc, MVariant, DispatchMsg, ExecuteMsg, MMsg
from lizard.util.rtl.interface import UseInterface
from lizard.util.rtl.pipeline_stage import DropControllerInterface, PipelineStageInterface
from lizard.util.rtl.killable_pipeline_wrapper import InputPipelineAdapterInterface, OutputPipelineAdapterInterface, PipelineWrapper
from lizard.core.rtl.kill_unit import PipelineKillDropController
from lizard.core.rtl.controlflow import KillType
from lizard.util.rtl.multiply import MulPipelined, MulPipelinedInterface


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
  return Bits(2 * XLEN)


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
    s.multiplier = MulPipelined(
        MulPipelinedInterface(XLEN, keep_upper=True),
        nstages=num_stages,
        use_mul=True)

    # PYMTL_BROKEN
    # double array in combinational block
    s.in_peek_msg_a = Wire(XLEN)
    s.in_peek_msg_b = Wire(XLEN)
    s.connect(s.in_peek_msg_a, s.in_peek_msg.a)
    s.connect(s.in_peek_msg_b, s.in_peek_msg.b)

    s.op32_a = Wire(32)
    s.op32_b = Wire(32)

    @s.combinational
    def set_inputs():
      s.op32_a.v = s.in_peek_msg_a[:32]
      s.op32_b.v = s.in_peek_msg_b[:32]
      s.multiplier.mult_src1_signed.v = not (
          s.in_peek_msg.variant == MVariant.M_VARIANT_U or
          s.in_peek_msg.variant == MVariant.M_VARIANT_HU)
      s.multiplier.mult_src2_signed.v = (
          s.in_peek_msg.variant == MVariant.M_VARIANT_N or
          s.in_peek_msg.variant == MVariant.M_VARIANT_H)
      if s.in_peek_msg.op32:
        s.multiplier.mult_src1.v = sext(s.op32_a, XLEN)
        s.multiplier.mult_src2.v = sext(s.op32_b, XLEN)
      else:
        s.multiplier.mult_src1.v = s.in_peek_msg.a
        s.multiplier.mult_src2.v = s.in_peek_msg.b

    s.connect(s.multiplier.mult_call, s.in_take_call)

    @s.combinational
    def set_in_take_call():
      s.in_take_call.v = s.multiplier.mult_rdy and s.in_peek_rdy

    # Connect output
    s.connect(s.multiplier.take_call, s.take_call)
    s.connect(s.peek_rdy, s.multiplier.peek_rdy)
    s.connect(s.peek_msg, s.multiplier.peek_res)


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
      s.split_kill_data.result.v = zext(s.split_in_.m_msg, XLEN)
      s.split_kill_data.rd.v = s.split_in_.rd
      s.split_kill_data.rd_val.v = s.split_in_.rd_val


def MultOutputPipelineAdapterInterface():
  return OutputPipelineAdapterInterface(MultOut(), ExecuteMsg(), ExecuteMsg())


class MultOutputPipelineAdapter(Model):

  def __init__(s):
    UseInterface(s, MultOutputPipelineAdapterInterface())

    s.out_temp = Wire(s.interface.Out)
    s.out_mmsg = Wire(MMsg())
    s.out_32 = Wire(32)
    # PYMTL_BROKEN
    # Use temporary wire to prevent pymtl bug
    num_bits = MMsg().nbits

    # PYMTL_BROKEN
    # 2D array bug
    s.fuse_kill_data_result = Wire(XLEN)

    @s.combinational
    def connect_wire_workaround():
      s.fuse_kill_data_result.v = s.fuse_kill_data.result

    @s.combinational
    def compute_out(XLEN_2=2 * XLEN, num_bits=num_bits):
      s.out_mmsg.v = s.fuse_kill_data_result[:num_bits]  # Magic cast
      s.out_temp.v = s.fuse_kill_data
      s.out_32.v = s.fuse_internal_out[:32]
      if s.out_mmsg.op32:
        s.out_temp.result.v = sext(s.out_32, XLEN)
      elif s.out_mmsg.variant == MVariant.M_VARIANT_N or s.out_mmsg.variant == MVariant.M_VARIANT_U:
        s.out_temp.result.v = s.fuse_internal_out[:XLEN]
      else:
        s.out_temp.result.v = s.fuse_internal_out[XLEN:XLEN_2]

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
