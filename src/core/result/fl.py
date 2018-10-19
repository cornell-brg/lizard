from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.result import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL


class ResultFL(Model):
    def __init__(s, dataflow, controlflow):
        s.result_in = InValRdyBundle(FunctionalPacket())
        s.result_out = OutValRdyBundle(ResultPacket())

        s.result_in_q = InValRdyQueueAdapterFL(s.result_in)
        s.result_out_q = OutValRdyQueueAdapterFL(s.result_out)

        s.dataflow = dataflow
        s.controlflow = controlflow

        @s.tick_fl
        def tick():
            p = s.result_in_q.popleft()

            # verify instruction still alive
            creq = TagValidRequest()
            creq.tag = p.tag
            cresp = s.controlflow.tag_valid(creq)
            if not cresp.valid:
                # if we allocated a destination register for this instruction,
                # we must free it
                if p.rd_valid:
                    s.dataflow.free_tag(p.rd)
                # retire instruction from controlflow
                creq = RetireRequest()
                creq.tag = p.tag
                s.controlflow.retire(creq)
                return

            if p.rd_valid:
                dataflow.write_tag(p.rd, p.result)

            out = ResultPacket()
            out.inst = p.inst
            out.rd_valid = p.rd_valid
            out.result.rd = p.rd
            out.result = p.result
            out.pc = p.pc
            out.tag = p.tag

            s.result_out_q.append(out)

    def line_trace(s):
        return "No line trace for you!"
