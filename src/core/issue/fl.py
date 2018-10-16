from pymtl import *
from msg.decode import *
from msg.issue import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR, REG_COUNT


class IssueFL(Model):
    def __init__(s, dataflow):
        s.decoded = InValRdyBundle(DecodePacket())
        s.issued = OutValRdyBundle(IssuePacket())

        s.decoded_q = InValRdyQueueAdapterFL(s.decoded)
        s.issued_q = OutValRdyQueueAdapterFL(s.issued)

        s.dataflow = dataflow

        @s.tick_fl
        def tick():
            if s.reset:
                s.current = None
                s.current_rs1 = None
                s.current_rs2 = None

            if not s.current:
                s.current_d = s.decoded_q.popleft()
                s.current_i = IssuePacket()

            if s.current_d.rd_valid and not s.current_i.rd_valid:
                dst = s.dataflow.get_dst(s.current_d.rd)
                s.current_i.rd_valid = dst.success
                s.current_i.rd = dst.tag

            if s.current_d.rs1_valid and not s.current_i.rs1_valid and not s.current_rs1:
                src = s.dataflow.get_src(s.current_d.rs1)
                s.current_rs1 = src.tag
                print('renamed src: {} -> {}'.format(s.current_d.rs1, src.tag))
            if s.current_rs1 is not None and not s.current_i.rs1_valid:
                read = s.dataflow.read_tag(s.current_rs1)
                s.current_i.rs1 = read.value
                s.current_i.rs1_valid = read.ready
                if s.current_i.rs1_valid:
                    print('got rs1 value: {}'.format(s.current_i.rs1))

            if s.current_d.rs2_valid and not s.current_i.rs2_valid:
                src = s.dataflow.get_src(s.current_d.rs2)
                s.current_i.rs2_valid = src.ready
                if src.ready:
                    s.current_i.rs2 = s.dataflow.read_tag(src.tag).value

            # Done if all fields are as they should be
            if s.current_d.rd_valid == s.current_i.rd_valid and s.current_d.rs1_valid == s.current_i.rs1_valid and s.current_d.rs2_valid == s.current_i.rs2_valid:
                s.current_i.imm = s.current_d.imm
                s.current_i.inst = s.current_d.inst
                s.current_i.csr = s.current_d.csr
                s.current_i.csr_valid = s.current_d.csr_valid
                s.issued_q.append(s.current_i)
                s.current_d = None
                s.current_rs1 = None
                s.current_rs2 = None
                print('ISSUED ISSUED ISSUED ISSUED ISSUED ISSUED ISSUED ISSUED')

    def line_trace(s):
        return "0xDEADBEEF"
