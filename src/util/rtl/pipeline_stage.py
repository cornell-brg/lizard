from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array
from util.rtl.register import Register, RegisterInterface
from util.rtl.mux import Mux


class PipelineStageInterface(Interface):

  def __init__(s, MsgType):
    s.MsgType = MsgType
    # If there is no MsgType, this is the last pipeline stage and has no outputs
    if MsgType is None:
      methods = []
    else:
      methods = [
          MethodSpec(
              'peek',
              args=None,
              rets={
                  'msg': MsgType,
              },
              call=False,
              rdy=True,
          ),
          MethodSpec(
              'take',
              args=None,
              rets=None,
              call=True,
              rdy=False,
          ),
      ]
    super(PipelineStageInterface, s).__init__(methods)


class StageInterface(Interface):

  def __init__(s, In, Out):
    s.In = In
    s.Out = Out
    # If this is the first pipeline stage, it takes no arguments
    if In is None:
      args = {}
    else:
      args = {'in_': In}
    # If this is the last pipeline stage, it produces nothing
    if Out is None:
      rets = {}
    else:
      rets = {'out': Out}
    rets['accepted'] = Bits(1)
    super(StageInterface, s).__init__([
        MethodSpec(
            'process',
            args=args,
            rets=rets,
            call=True,
            rdy=False,
        ),
    ])


class DropControllerInterface(Interface):

  def __init__(s, In):
    s.In = In
    super(DropControllerInterface, s).__init__([
        MethodSpec(
            'check',
            args={
                'in_': In,
            },
            rets={
                'keep': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class PipelineStage(Model):

  def __init__(s, interface, In):
    UseInterface(s, interface)
    # Require the methods of an incoming pipeline stage
    # Note that if In is None, the incoming stage will have no methods
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name))
        for m in PipelineStageInterface(In).methods.values()
    ])
    s.require(StageInterface(In, interface.MsgType)['process'])
    # If this pipeline stage outputs, require a drop controller
    if interface.MsgType is not None:
      s.require(DropControllerInterface(interface.MsgType)['check'])
      s.out_reg = Register(RegisterInterface(interface.MsgType, enable=True))
      s.val_mux = Mux(1, 2)
      s.val_reg = Register(RegisterInterface(Bits(1)), reset_value=0)
      s.rdy_mux = Mux(1, 2)
      s.val_after_drop_mux = Mux(1, 2)

    s.input_available = Wire(1)
    s.output_clear = Wire(1)
    s.advance = Wire(1)
    s.taking = Wire(1)

    @s.combinational
    def handle_taking():
      s.taking.v = s.advance & s.process_accepted

    s.connect(s.process_call, s.advance)
    if In is not None:
      s.connect(s.process_in_, s.in_peek_msg)
      s.connect(s.in_take_call, s.taking)
      s.connect(s.input_available, s.in_peek_rdy)
    else:
      s.connect(s.input_available, 1)
    if interface.MsgType is not None:
      s.connect(s.out_reg.write_data, s.process_out)
      s.connect(s.out_reg.write_call, s.taking)

      s.connect(s.val_after_drop_mux.mux_in_[0], 0)
      s.connect(s.val_after_drop_mux.mux_in_[1], s.check_keep)
      s.connect(s.val_after_drop_mux.mux_select, s.val_reg.read_data)
      s.connect(s.val_mux.mux_in_[0], s.val_after_drop_mux.mux_out)
      s.connect(s.val_mux.mux_in_[1], 1)
      s.connect(s.val_mux.mux_select, s.taking)
      s.connect(s.val_reg.write_data, s.val_mux.mux_out)

      s.connect(s.check_in_, s.out_reg.read_data)
      s.connect(s.peek_msg, s.out_reg.read_data)
      s.connect(s.rdy_mux.mux_in_[0], 0)
      s.connect(s.rdy_mux.mux_in_[1], s.check_keep)
      s.connect(s.rdy_mux.mux_select, s.val_reg.read_data)
      s.connect(s.peek_rdy, s.rdy_mux.mux_out)

    if interface.MsgType is not None:

      @s.combinational
      def handle_output_clear():
        s.output_clear.v = s.take_call or not s.val_after_drop_mux.mux_out
    else:
      s.connect(s.output_clear, 1)

    @s.combinational
    def handle_advance():
      s.advance.v = s.output_clear and s.input_available


def gen_stage(stage_class, drop_controller_class=None):
  name = ''.join([
      '{}L{}'.format(len(class_.__name__), class_.__name__)
      for class_ in [stage_class, drop_controller_class]
  ])
  name = 'GS{}'.format(name)

  class Pipelined(Model):

    def __init__(s):
      s.stage = stage_class()
      UseInterface(s, PipelineStageInterface(s.stage.interface.Out))
      s.pipeline_stage = PipelineStage(s.interface, s.stage.interface.In)
      assert (s.stage.interface.Out is None) == (drop_controller_class is None)
      if drop_controller_class is not None:
        s.drop_controller = drop_controller_class()
        s.connect_m(s.pipeline_stage.check, s.drop_controller.check)
      s.connect_m(s.pipeline_stage.process, s.stage.process)
      s.connect_m(s.pipeline_stage.peek, s.peek)
      s.connect_m(s.pipeline_stage.take, s.take)

      if s.stage.interface.In is not None:
        # Require the methods of an incoming pipeline stage
        # Note that if In is None, the incoming stage will have no methods
        # Name the methods in_peek, in_take
        ins = [
            m.variant(name='in_{}'.format(m.name)) for m in
            PipelineStageInterface(s.stage.interface.In).methods.values()
        ]
        s.require(*ins)
        for method in ins:
          s.connect_m(
              getattr(s.pipeline_stage, method.name), getattr(s, method.name))

  Pipelined.__name__ = name
  return Pipelined
