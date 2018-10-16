from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.result import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL


class ResultFL(Model):
    def __init__(s, dataflow):
        s.result_in = InValRdyBundle(FunctionalPacket())
        s.result_out = OutValRdyBundle(ResultPacket())

        s.result_in_q = InValRdyQueueAdapterFL(s.result_in)
        s.result_out_q = OutValRdyQueueAdapterFL(s.result_out)

        s.dataflow = dataflow

        @s.tick_fl
        def tick():
            p = result_in_q.popleft()

            if p.rd_valid:
                dataflow.write_tag(p.rd, p.result)

            out = ResultPacket()
            out.inst = p.inst
            out.rd_valid = p.rd_valid
            out.result.rd = p.rd
            out.result = p.result

            result_out_q.append(out)

    def line_trace(s):
        return "No line trace for you!"
