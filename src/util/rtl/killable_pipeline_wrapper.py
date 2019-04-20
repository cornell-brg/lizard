from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array
from util.rtl.register import Register, RegisterInterface
from util.rtl.pipeline_stage import PipelineStageInterface, ValidValueManager, ValidValueManagerInterface, gen_valid_value_manager

KillablePipelineWrapperInterface = PipelineStageInterface


class InputPipelineAdapterInterface(Interface):

  def __init__(s, In, InternalIn, KillData):
    s.In = In
    s.InternalIn = InternalIn
    s.KillData = KillData

    super(InputPipelineAdapterInterface, s).__init__([
        MethodSpec(
            'split',
            args={
                'in_': In,
            },
            rets={
                'internal_in': InternalIn,
                'kill_data': KillData,
            },
            call=False,
            rdy=False,
        ),
    ])


class OutputPipelineAdapterInterface(Interface):

  def __init__(s, InternalOut, KillData, Out):
    s.InternalOut = InternalOut
    s.KillData = KillData
    s.Out = Out

    super(OutputPipelineAdapterInterface, s).__init__([
        MethodSpec(
            'fuse',
            args={
                'internal_out': InternalOut,
                'kill_data': KillData,
            },
            rets={
                'out': Out,
            },
            call=False,
            rdy=False,
        ),
    ])


class PipelineWrapper(Model):

  def __init__(s, interface, nstages, InputPipelineAdapter, InternalPipeline,
               OutputPipelineAdapter, DropController):
    UseInterface(s, interface)

    s.input_adapter = InputPipelineAdapter()
    s.internal_pipeline = InternalPipeline()
    s.wrap(s.internal_pipeline, ['in_peek', 'in_take'])
    s.output_adapter = OutputPipelineAdapter()
    s.KillData = s.input_adapter.interface.KillData
    s.KillArgType = s.interface.KillArgType

    # Generate tracking ValidValueManagers which do not drop packets
    # but rather mark them with a dead flag
    s.ValidValueManager = gen_valid_value_manager(DropController, tracking=True)
    s.vvms = [s.ValidValueManager() for _ in range(nstages)]

    # Require the methods of an incoming pipeline stage
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name)) for m in PipelineStageInterface(
            s.input_adapter.interface.In, None).methods.values()
    ])

    s.connect(s.internal_pipeline.in_peek_rdy, s.in_peek_rdy)
    s.connect(s.input_adapter.split_in_, s.in_peek_msg)
    s.connect(s.internal_pipeline.in_peek_msg,
              s.input_adapter.split_internal_in)
    s.connect(s.in_take_call, s.internal_pipeline.in_take_call)

    s.connect(s.vvms[0].add_call, s.internal_pipeline.in_take_call)
    s.connect(s.vvms[0].add_msg, s.input_adapter.split_kill_data)
    s.connect(s.vvms[0].add_dead, 0)

    for i in range(1, nstages):
      s.connect(s.vvms[i].add_msg, s.vvms[i - 1].peek_msg)
      s.connect(s.vvms[i].add_dead, s.vvms[i - 1].peek_dead)

      @s.combinational
      def handle_shift(i=i, j=i - 1):
        s.vvms[j].take_call.v = s.vvms[j].peek_rdy and s.vvms[i].add_rdy
        s.vvms[i].add_call.v = s.vvms[j].take_call

    for i in range(nstages):
      s.connect_m(s.vvms[i].kill_notify, s.kill_notify)

    s.connect(s.output_adapter.fuse_internal_out, s.internal_pipeline.peek_msg)
    s.connect(s.output_adapter.fuse_kill_data, s.vvms[-1].peek_msg)
    s.connect(s.peek_msg, s.output_adapter.fuse_out)

    @s.combinational
    def handle_output_peek_take(i=nstages - 1):
      # If we have something at the end of both pipeline
      if s.internal_pipeline.peek_rdy and s.vvms[i].peek_rdy:
        # If the thing has not been killed
        if not s.vvms[i].peek_dead:
          s.peek_rdy.v = 1
          s.internal_pipeline.take_call.v = s.take_call
          s.vvms[i].take_call.v = s.take_call
        else:
          s.peek_rdy.v = 0
          # Eat the message from the internal pipeline
          s.internal_pipeline.take_call.v = 1
          s.vvms[i].take_call.v = 1
      else:
        s.peek_rdy.v = 0
        s.internal_pipeline.take_call.v = 0
        s.vvms[i].take_call.v = 0

  def line_trace(s):
    return s.internal_pipeline.line_trace()
