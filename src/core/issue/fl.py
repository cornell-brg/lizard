from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR, REG_COUNT


class IssueFL(Model):
    def __init__(s, dataflow, controlflow):
        s.decoded = InValRdyBundle(DecodePacket())
        s.issued = OutValRdyBundle(IssuePacket())

        s.decoded_q = InValRdyQueueAdapterFL(s.decoded)
        s.issued_q = OutValRdyQueueAdapterFL(s.issued)

        s.dataflow = dataflow
        s.controlflow = controlflow

        s.current_i = IssuePacket()

        @s.tick_fl
        def tick():
            if s.reset:
                s.current_d = None

            if s.current_d is None:
                s.current_d = s.decoded_q.popleft()
                s.current_i = IssuePacket()
                s.current_rs1 = None
                s.current_rs2 = None
                s.marked_speculative = False

            # verify instruction still alive
            creq = TagValidRequest()
            creq.tag = s.current_d.tag
            cresp = s.controlflow.tag_valid(creq)
            if not cresp.valid:
                # if we allocated a destination register for this instruction,
                # we must free it
                if s.current_i.rd_valid:
                    s.dataflow.free_tag(c.current_i.rd)
                # retire instruction from controlflow
                creq = RetireRequest()
                creq.tag = s.current_d.tag
                s.controlflow.retire(creq)

                s.current_d = None
                return

            # if the instruction has potential to redirect early (before commit)
            # must declare instruction to controlflow
            # (essentialy creates a rename table snapshot)
            # TODO: support more than BEQ
            if not s.marked_speculative and s.current_d.inst == RV64Inst.BEQ:
                creq = MarkSpeculativeRequest()
                creq.tag = s.current_d.tag
                cresp = s.controlflow.mark_speculative(creq)
                if cresp.success:
                    s.marked_speculative = True
                else:
                    # if we failed to mark it speculative
                    # (likely because we are too deeply in speculation right now)
                    # must stall
                    return

            if s.current_d.rs1_valid and s.current_rs1 is None:
                src = s.dataflow.get_src(s.current_d.rs1)
                s.current_rs1 = src.tag

            if s.current_rs1 is not None and not s.current_i.rs1_valid:
                read = s.dataflow.read_tag(s.current_rs1)
                s.current_i.rs1 = read.value
                s.current_i.rs1_valid = read.ready

            if s.current_d.rs2_valid and s.current_rs2 is None:
                src = s.dataflow.get_src(s.current_d.rs2)
                s.current_rs2 = src.tag

            if s.current_rs2 is not None and not s.current_i.rs2_valid:
                read = s.dataflow.read_tag(s.current_rs2)
                s.current_i.rs2 = read.value
                s.current_i.rs2_valid = read.ready

            # Must get sources before renaming destination!
            # Otherwise consider ADDI x1, x1, 1
            # If you rename the destination first, the instruction is waiting for itself
            if s.current_d.rd_valid and not s.current_i.rd_valid:
                dst = s.dataflow.get_dst(s.current_d.rd)
                s.current_i.rd_valid = dst.success
                s.current_i.rd = dst.tag

            # Done if all fields are as they should be
            if s.current_d.rd_valid == s.current_i.rd_valid and s.current_d.rs1_valid == s.current_i.rs1_valid and s.current_d.rs2_valid == s.current_i.rs2_valid:
                s.current_i.imm = s.current_d.imm
                s.current_i.inst = s.current_d.inst
                s.current_i.csr = s.current_d.csr
                s.current_i.csr_valid = s.current_d.csr_valid
                s.current_i.pc = s.current_d.pc
                s.current_i.tag = s.current_d.tag
                s.issued_q.append(s.current_i)
                s.current_d = None

    def line_trace(s):
        return s.current_i
