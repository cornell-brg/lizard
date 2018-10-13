from pymtl import *
from msg.decode import *
from msg.data import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR, REG_COUNT


class IssueFL(Model):
    def __init__(s, dataflow):
        s.decoded = InValRdyBundle(DecodePacket())

        @s.tick_fl
        def tick():
            decoded = s.decoded_q.popleft()
            result = DataUnitResponse()
            if decoded.rs1.reg.valid:
                result.rs1.value = s.reg_file[decoded.rs1.reg.id]
            if decoded.rs2.reg.valid:
                result.rs2.value = s.reg_file[decoded.rs1.reg.id]
            result.rs1.reg = deocded.rs1.reg
            result.rs2.reg = decoded.rs2.reg
            s.decoded_q.append(result)

    def line_trace(s):
        return "¯\_(ツ)_/¯"
