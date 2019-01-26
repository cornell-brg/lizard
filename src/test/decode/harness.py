import struct
import inspect

from pymtl import *
from pclib.test import TestSource, TestSink
from pclib.cl import InValRdyQueueAdapter, OutValRdyQueueAdapter
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from msg.datapath import *


class Harness(Model):

  def __init__(s, DispatchModel, src_msgs, sink_msgs, dump_vcd):
    # interfaces
    s.src = TestSource(FetchPacket(), src_msgs, 5)
    s.sink = TestSink(DecodePacket(), sink_msgs, 5)

    s.dispatch_unit = DispatchModel(None)

    s.connect(s.src.out, s.dispatch_unit.instr)
    s.connect(s.dispatch_unit.decoded, s.sink.in_)

  def done(s):
    return s.src.done and s.sink.done

  def line_trace(s):
    return s.src.line_trace() + " > " + s.dispatch_unit.line_trace(
    ) + " > " + s.sink.line_trace()
