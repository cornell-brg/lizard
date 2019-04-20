from pymtl import *
from util.rtl.interface import Interface, UseInterface
from core.rtl.backend.divide import Div
from core.rtl.backend.multiply import Mult
from core.rtl.messages import MFunc, MVariant, DispatchMsg, ExecuteMsg
from util.rtl.pipeline_stage import gen_stage, StageInterface, DropControllerInterface, PipelineStageInterface, gen_valid_value_manager
from core.rtl.controlflow import KillType
from config.general import *


def MPipeInterface():
  return PipelineStageInterface(ExecuteMsg(), KillType(MAX_SPEC_DEPTH))


class MPipe(Model):

  def __init__(s):
    UseInterface(s, MPipeInterface())

    # Require the methods of an incoming pipeline stage
    # Name the methods in_peek, in_take
    s.require(*[
        m.variant(name='in_{}'.format(m.name))
        for m in PipelineStageInterface(DispatchMsg(), None).methods.values()
    ])

    s.div = Div()
    s.mult = Mult()

    s.connect(s.div.in_peek_msg, s.in_peek_msg)
    s.connect(s.mult.in_peek_msg, s.in_peek_msg)
    s.connect_m(s.div.kill_notify, s.kill_notify)
    s.connect_m(s.mult.kill_notify, s.kill_notify)

    @s.combinational
    def route_input():
      if s.in_peek_msg.m_msg_func == MFunc.M_FUNC_MUL:
        s.mult.in_peek_rdy.v = s.in_peek_rdy
        s.in_take_call.v = s.mult.in_take_call
        s.div.in_peek_rdy.v = 0
      else:
        s.div.in_peek_rdy.v = s.in_peek_rdy
        s.in_take_call.v = s.div.in_take_call
        s.mult.in_peek_rdy.v = 0

    @s.combinational
    def route_output():
      if s.div.peek_rdy:
        s.peek_rdy.v = s.div.peek_rdy
        s.peek_msg.v = s.div.peek_msg
        s.div.take_call.v = s.take_call
        s.mult.take_call.v = 0
      else:
        s.peek_rdy.v = s.mult.peek_rdy
        s.peek_msg.v = s.mult.peek_msg
        s.mult.take_call.v = s.take_call
        s.div.take_call.v = 0

  def line_trace(s):
    incoming = s.in_peek_msg.hdr_seq.hex()[2:]
    if not s.in_take_call:
      incoming = ' ' * len(incoming)
    if s.take_call:
      outgoing_status = '*'
    elif s.peek_rdy:
      outgoing_status = '#'
    else:
      outgoing_status = ' '
    outgoing = s.peek_msg.hdr_seq.hex()[2:]
    if not s.peek_rdy:
      outgoing = ' ' * len(outgoing)
    return '{} : {} {}'.format(incoming, outgoing_status, outgoing)
