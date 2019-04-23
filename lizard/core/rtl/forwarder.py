from pymtl import *
from lizard.config.general import *
from lizard.util.rtl.interface import Interface, IncludeAll, UseInterface
from lizard.core.rtl.messages import ExecuteMsg, PipelineMsgStatus
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.pipeline_stage import PipelineStageInterface, gen_stage, NullDropController


class ForwarderInterface(Interface):

  def __init__(s):
    super(ForwarderInterface, s).__init__(
        [
            MethodSpec(
                'in_forward',
                args={
                    'tag': PREG_IDX_NBITS,
                    'value': Bits(XLEN),
                },
                rets=None,
                call=True,
                rdy=False,
            )
        ],
        bases=[IncludeAll(PipelineStageInterface(ExecuteMsg(), None))],
    )


class Forwarder(Model):

  def __init__(s):
    UseInterface(s, ForwarderInterface())
    s.require(
        MethodSpec(
            'in_peek',
            args=None,
            rets={
                'msg': ExecuteMsg(),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'in_take',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'forward',
            args={
                'tag': PREG_IDX_NBITS,
                'value': Bits(XLEN),
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    )

    s.connect_m(s.peek, s.in_peek)
    s.connect_m(s.take, s.in_take)

    @s.combinational
    def handle_forward():
      if s.in_forward_call:
        s.forward_tag.v = s.in_forward_tag
        s.forward_value.v = s.in_forward_value
        s.forward_call.v = s.in_forward_call
      else:
        s.forward_tag.v = s.in_peek_msg.rd
        s.forward_value.v = s.in_peek_msg.result
        s.forward_call.v = s.in_peek_rdy and s.in_peek_msg.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID and s.in_peek_msg.rd_val


class ForwardingStage(Model):

  def __init__(s, internal_stage):
    s.stage = internal_stage()
    UseInterface(s, s.stage.interface)
    s.require(
        MethodSpec(
            'forward',
            args={
                'tag': PREG_IDX_NBITS,
                'value': Bits(XLEN),
            },
            rets=None,
            call=True,
            rdy=False,
        ),)

    s.connect_m(s.process, s.stage.process)
    s.wrap(s.stage)

    @s.combinational
    def handle_forward():
      s.forward_tag.v = s.process_out.rd
      s.forward_value.v = s.process_out.result
      s.forward_call.v = s.process_call and s.process_accepted and s.process_out.hdr_status == PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID and s.process_out.rd_val

  def line_trace(s):
    return s.stage.line_trace()


class ForwardingPipelineStage(Model):

  def __init__(s, stage_class, drop_controller_class=None):

    def gen():
      return ForwardingStage(stage_class)

    gen.__name__ = stage_class.__name__
    s.gen_stage = gen_stage(gen, drop_controller_class)()
    UseInterface(s, s.gen_stage.interface)
    s.wrap(s.gen_stage, ['forward'])
    s.require(
        MethodSpec(
            'forward',
            args={
                'tag': PREG_IDX_NBITS,
                'value': Bits(XLEN),
            },
            rets=None,
            call=True,
            rdy=False,
        ),)

    s.forwarder = Forwarder()
    s.connect_m(s.forwarder.in_forward, s.gen_stage.forward)
    s.connect_m(s.forwarder.in_peek, s.gen_stage.peek)
    s.connect_m(s.forwarder.in_take, s.gen_stage.take)
    s.connect_m(s.forward, s.forwarder.forward)
    s.connect_m(s.peek, s.forwarder.peek)
    s.connect_m(s.take, s.forwarder.take)

    if hasattr(s, 'kill_notify'):
      s.connect_m(s.gen_stage.kill_notify, s.kill_notify)

  def line_trace(s):
    return s.gen_stage.line_trace()


def gen_forwarding_stage(stage_class, drop_controller_class=None):
  name = ''.join([
      '{}L{}'.format(len(class_.__name__), class_.__name__) for class_ in [
          stage_class, drop_controller_class
          if drop_controller_class is not None else NullDropController
      ]
  ])
  name = 'GFS{}'.format(name)

  def gen():
    return ForwardingPipelineStage(stage_class, drop_controller_class)

  gen.__name__ = name
  return gen
