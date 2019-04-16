from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array
from util.rtl.register import Register, RegisterInterface
from util.rtl.mux import Mux
from util.rtl.types import Array, canonicalize_type


class PipelineStageInterface(Interface):

  def __init__(s, MsgType, KillArgType):
    s.MsgType = MsgType
    s.KillArgType = KillArgType
    methods = []
    if KillArgType is not None:
      methods.append(
          MethodSpec(
              'kill_notify',
              args={
                  'msg': KillArgType,
              },
              rets=None,
              call=False,
              rdy=False,
          ),)
    # If there is no MsgType, this is the last pipeline stage and has no outputs
    if MsgType is not None:
      methods.extend([
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
      ])
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

  def __init__(s, In, Out, KillArgType):
    s.In = canonicalize_type(In)
    s.Out = canonicalize_type(Out)
    s.KillArgType = canonicalize_type(KillArgType)
    check_args = {'in_': In}
    if KillArgType is not None:
      check_args['msg'] = KillArgType
    super(DropControllerInterface, s).__init__([
        MethodSpec(
            'check',
            args=check_args,
            rets={
                'out': Out,
                'keep': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class NullDropController(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.connect(s.check_keep, 1)
    s.connect(s.check_out, s.check_in_)


class ValidValueManagerInterface(Interface):

  def __init__(s, DataIn, DataOut, KillArgType):
    s.DataIn = DataIn
    s.DataOut = DataOut
    s.KillArgType = KillArgType
    if KillArgType is not None:
      first = [
          MethodSpec(
              'kill_notify',
              args={
                  'msg': KillArgType,
              },
              rets=None,
              call=False,
              rdy=False,
          ),
      ]
    else:
      first = []

    methods = first + [
        MethodSpec(
            'dropping',
            args=None,
            rets={
                'out': Bits(1),
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'peek',
            args=None,
            rets={
                'msg': DataOut,
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
        MethodSpec(
            'add',
            args={
                'msg': DataIn,
            },
            rets=None,
            call=True,
            rdy=True,
        ),
    ]

    super(ValidValueManagerInterface, s).__init__(methods)


class ValidValueManager(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    s.require(
        DropControllerInterface(s.interface.DataIn, s.interface.DataOut,
                                s.interface.KillArgType)['check'])

    s.val_reg = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.out_reg = Register(RegisterInterface(s.interface.DataIn))
    s.output_rdy = Wire(1)
    s.output_clear = Wire(1)

    if s.interface.KillArgType is not None:
      s.connect(s.check_msg, s.kill_notify_msg)
    s.connect(s.check_in_, s.out_reg.read_data)
    s.connect(s.peek_msg, s.check_out)

    @s.combinational
    def handle_rdy():
      if s.val_reg.read_data:
        s.output_rdy.v = s.check_keep
        s.dropping_out.v = not s.check_keep
      else:
        s.output_rdy.v = 0
        s.dropping_out.v = 0

    s.connect(s.peek_rdy, s.output_rdy)

    @s.combinational
    def handle_clear():
      s.output_clear.v = not s.output_rdy or s.take_call

    s.connect(s.add_rdy, s.output_clear)

    @s.combinational
    def handle_val_reg_in():
      if s.add_call:
        s.val_reg.write_data.v = 1
      else:
        s.val_reg.write_data.v = not s.output_clear

    @s.combinational
    def handle_out_reg():
      if s.add_call:
        s.out_reg.write_data.v = s.add_msg
      else:
        s.out_reg.write_data.v = s.check_out


def gen_valid_value_manager(drop_controller_class):
  name = ''.join([
      '{}L{}'.format(len(class_.__name__), class_.__name__)
      for class_ in [drop_controller_class]
  ])
  name = 'GenValidValueManager{}'.format(name)

  class Gen(Model):

    def __init__(s):
      s.drop_controller = drop_controller_class()
      UseInterface(
          s,
          ValidValueManagerInterface(s.drop_controller.interface.In,
                                     s.drop_controller.interface.Out,
                                     s.drop_controller.interface.KillArgType))

      s.manager = ValidValueManager(s.interface)
      s.connect_m(s.manager.check, s.drop_controller.check)
      if s.interface.KillArgType is not None:
        s.connect_m(s.manager.kill_notify, s.kill_notify)
      s.connect_m(s.manager.peek, s.peek)
      s.connect_m(s.manager.take, s.take)
      s.connect_m(s.manager.add, s.add)

  Gen.__name__ = name
  return Gen


class PipelineStage(Model):

  def __init__(s, interface, In, Intermediate=None):
    UseInterface(s, interface)
    # Assume intermediate type is same as output unless specified
    Intermediate = Intermediate or s.interface.MsgType
    # Require the methods of an incoming pipeline stage
    # Note that if In is None, the incoming stage will have no methods
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name))
        for m in PipelineStageInterface(In, None).methods.values()
    ])
    s.require(StageInterface(In, interface.MsgType)['process'])
    # If this pipeline stage outputs, require a drop controller
    if interface.MsgType is not None:
      s.require(
          DropControllerInterface(interface.MsgType, Intermediate,
                                  interface.KillArgType)['check'])
      s.vvm = ValidValueManager(
          ValidValueManagerInterface(interface.MsgType, Intermediate,
                                     interface.KillArgType))

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
      s.connect(s.vvm.add_msg, s.process_out)
      s.connect(s.vvm.add_call, s.taking)
      if s.interface.KillArgType is not None:
        s.connect_m(s.vvm.kill_notify, s.kill_notify)
      s.connect_m(s.vvm.check, s.check)
      s.connect_m(s.vvm.peek, s.peek)
      s.connect_m(s.vvm.take, s.take)

      s.connect(s.output_clear, s.vvm.add_rdy)
    else:
      s.connect(s.output_clear, 1)

    @s.combinational
    def handle_advance():
      s.advance.v = s.output_clear and s.input_available


def gen_stage(stage_class, drop_controller_class=None):
  name = ''.join([
      '{}L{}'.format(len(class_.__name__), class_.__name__) for class_ in [
          stage_class, drop_controller_class
          if drop_controller_class is not None else NullDropController
      ]
  ])
  name = 'GS{}'.format(name)

  class Pipelined(Model):

    def __init__(s, *args, **kwargs):
      s.stage = stage_class(*args, **kwargs)
      actual_dc = drop_controller_class
      if s.stage.interface.Out is not None and drop_controller_class is None:

        def gen_drop_controller():
          return NullDropController(
              DropControllerInterface(s.stage.interface.Out,
                                      s.stage.interface.Out, None))

        actual_dc = gen_drop_controller
      assert not (s.stage.interface.Out is None and actual_dc is not None)
      if actual_dc is not None:
        s.drop_controller = actual_dc()
        KillArgType = s.drop_controller.interface.KillArgType
      else:
        KillArgType = None
      UseInterface(s, PipelineStageInterface(s.stage.interface.Out,
                                             KillArgType))
      s.pipeline_stage = PipelineStage(s.interface, s.stage.interface.In)

      if actual_dc is not None:
        s.drop_controller = actual_dc()
        s.connect_m(s.pipeline_stage.check, s.drop_controller.check)
        s.connect_m(s.pipeline_stage.process, s.stage.process)
        if s.interface.KillArgType is not None:
          s.connect_m(s.pipeline_stage.kill_notify, s.kill_notify)
        s.connect_m(s.pipeline_stage.peek, s.peek)
        s.connect_m(s.pipeline_stage.take, s.take)
      if s.stage.interface.In is not None:
        ins = [
            m.variant(name='in_{}'.format(m.name)) for m in
            PipelineStageInterface(s.stage.interface.In, None).methods.values()
        ]
        s.require(*ins)
        for method in ins:
          s.connect_m(
              getattr(s.pipeline_stage, method.name), getattr(s, method.name))

      s.wrap(s.stage)

    def line_trace(s):
      if s.pipeline_stage.advance:
        return '*'
      elif not s.pipeline_stage.output_clear:
        return '#'
      else:
        return ' '

  Pipelined.__name__ = name
  return Pipelined
