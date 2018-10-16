from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL


class FunctionalFL(Model):
    def __init__(s):
        s.issued = InValRdyBundle(IssuePacket())
        s.result = OutValRdyBundle(FunctionalPacket())

        s.issued_q = InValRdyQueueAdapterFL(s.issued)
        s.result_q = OutValRdyQueueAdapterFL(s.result)

        @s.tick_fl
        def tick():
            p = s.issued_q.popleft()

            out = FunctionalPacket()
            out.inst = p.inst
            out.rd_valid = p.rd_valid
            out.rd = p.rd

            if p.instr == RV64Inst.ADDI:
                out.result = p.rs1 + p.imm
            else:
                raise NotImplementedError('Can only do ADDI, sorry')

            result_q.append(out)

    def line_trace(s):
        return "No line trace for you!"
