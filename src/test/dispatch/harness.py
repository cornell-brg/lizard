import struct
import inspect

from pymtl import *

from msg import MemMsg4B
from msg.decode import DecodePacket
from pclib.test import TestSource, TestSink
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from msg.fetch import FetchPacket


class Harness(Model):
    def __init__(s, DispatchModel, src_msgs, sink_msgs, dump_vcd):
        # interfaces
        s.src = TestSource(FetchPacket(), src_msgs, 5)
        s.sink = TestSink(DecodePacket(), sink_msgs, 5)

        s.dispatch_unit = DispatchModel()

        s.connect(s.src.out, s.dispatch_unit.instr)
        s.connect(s.dispatch_unit.decoded, s.sink.in_)


    def done(s):
        return s.src.done and s.sink.done


    def line_trace(s):
        return s.src.line_trace() + " > " + s.dispatch_unit.line_trace() + " > " + s.sink.line_trace()
