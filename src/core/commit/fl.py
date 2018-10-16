from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.result import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL


class CommitFL(Model):
    def __init__(s, dataflow):
        s.result_in= InValRdyBundle(ResultPacket())
        s.result_in_q = InValRdyQueueAdapterFL(s.result_in)

        s.dataflow = dataflow

        @s.tick_fl
        def tick():
            p = result_in_q.popleft()

            if p.rd_valid:
                dataflow.commit_tag(p.rd)

    def line_trace(s):
        return "No line trace for you!"


