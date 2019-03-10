from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array
from util.rtl.register import Register


class PipelineStageInterface(Interface):

  def __init__(s, MsgType, count):
    s.MsgType = MsgType
    s.count = count
    # If there is no MsgType, this is the last pipeline stage and has no outputs
    if MsgType is None:
      methods = []
    else:
      methods = [
          MethodSpec(
              'peek',
              args={},
              rets={
                  'msg': Array(MsgType, count),
              },
              call=False,
              rdy=True,
          ),
          MethodSpec(
              'take',
              args={
                  'mask': Bits(count),
              },
              call=False,
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
    super(StageInterface, s).__init__([
        MethodSpec(
            'process',
            args=args,
            rets=rets,
            call=True,
            rdy=True,
        ),
    ])


class OutputConverterInterface(Interface):

  def __init__(s, In, Out):
    s.In = In
    s.Out = Out
    super(OutputConverterInterface, s).__init__([
        MethodSpec(
            'convert',
            args={
                'in_': In,
            },
            rets={
                'out': Out,
                'good': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class PipelineStage(Model):

  def __init__(s, interface, In, count, Intermediate):
    UseInterface(s, interface)
    # The intermediate type must be consistent with the output
    assert interface.MsgType is None == Intermediate is None
    # Require the methods of an incoming pipeline stage
    # Note that if In is None, the incoming stage will have no methods
    s.require(*PipelineStageInterface(In, count).methods.values())
    # Require the methods of a stage
    # Change the count to have enough
    s.require(StageInterface(In, Intermediate)['process'].variant(count=count))
    # If this pipeline stage outputs, require count output converters
    if interface.MsgType is not None:
      s.require(
          OutputConverterInterface(
              Intermediate, interface.MsgType)['convert'].variant(count=count))

    # Create the output pipeline registers if we have an output type
    if Intermediate is not None:
      s.out_regs = [Register(RegisterInterface(Intermediate, enable=True))]
      s.val_regs = [
          Register(RegisterInterface(Bits(1), enable=True), reset_value=0)
      ]
