from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL


class FunctionalFL(Model):
    def __init__(s, dataflow):
        s.issued = InValRdyBundle(IssuePacket())
        s.result = OutValRdyBundle(FunctionalPacket())

        s.issued_q = InValRdyQueueAdapterFL(s.issued)
        s.result_q = OutValRdyQueueAdapterFL(s.result)

        s.dataflow = dataflow

        @s.tick_fl
        def tick():
            p = s.issued_q.popleft()

            out = FunctionalPacket()
            out.inst = p.inst
            out.rd_valid = p.rd_valid
            out.rd = p.rd

            if p.inst == RV64Inst.ADDI:
                out.result = p.rs1 + sext(p.imm, XLEN)
            elif p.inst == RV64Inst.SLTI:
                if p.rs1.int() < p.imm.int():
                    out.result = 1
                else:
                    out.result = 0
            elif p.inst == RV64Inst.SLTIU:
                if p.rs1.uint() < p.imm.uint():
                    out.result = 1
                else:
                    out.result = 0
            elif p.inst == RV64Inst.XORI:
                out.result = p.rs1 ^ sext(p.imm, XLEN)
            elif p.inst == RV64Inst.ORI:
                out.result = p.rs1 | sext(p.imm, XLEN)
            elif p.inst == RV64Inst.ANDI:
                out.result = p.rs1 & sext(p.imm, XLEN)
            elif p.inst == RV64Inst.SLLI:
                out.result = p.rs1 << p.imm
            elif p.inst == RV64Inst.SRLI:
                out.result = Bits(
                    XLEN, p.rs1.uint() >> p.imm.uint(), trunc=True)
            elif p.inst == RV64Inst.SRAI:
                out.result = Bits(
                    XLEN, p.rs1.int() >> p.imm.uint(), trunc=True)
            elif p.inst == RV64Inst.CSRRW:
                if p.rd_valid:
                    out.result = s.dataflow.read_csr(p.csr)
                s.dataflow.write_csr(p.csr, p.rs1)
            elif p.inst == RV64Inst.CSRRS:
                out.result = s.dataflow.read_csr(p.csr)
                # TODO: not quite right because we should attempt to set
                # if the value of rs1 is zero but rs1 is not x0
                if p.rs1 != 0:
                    s.dataflow.write_csr(p.csr, out.result | p.rs1)
            else:
                raise NotImplementedError('Not implemented so sad: ' +
                                          RV64Inst.name(p.inst))

            out.pc = p.pc
            s.result_q.append(out)

    def line_trace(s):
        return "No line trace for you!"
