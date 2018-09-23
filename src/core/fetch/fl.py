#=========================================================================
# Integer Multiplier FL Model
#=========================================================================

from pymtl import *
from msg import MemMsg4B
from msg.fetch import FetchPacket
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR


class FetchFL(Model):
    def __init__(s):
        s.mem_req = OutValRdyBundle(MemMsg4B.req)
        s.mem_resp = InValRdyBundle(MemMsg4B.resp)
        s.instrs = OutValRdyBundle(FetchPacket())

        s.req_q = OutValRdyQueueAdapterFL(s.mem_req)
        s.resp_q = InValRdyQueueAdapterFL(s.mem_resp)
        s.instrs_q = OutValRdyQueueAdapterFL(s.instrs)

        s.pc = Wire(Bits(XLEN))
        s.last_pc = Wire(Bits(XLEN))

        @s.tick_fl
        def tick():
            if s.reset:
                s.pc.next = RESET_VECTOR
            else:
                s.req_q.append(MemMsg4B.req.mk_rd(0, s.pc.value, 0))
                mem_resp = s.resp_q.popleft()
                result = FetchPacket()
                result.stat = mem_resp.stat
                result.len = 0
                result.instr = mem_resp.data
                result.pc = s.pc.value
                s.instrs_q.append(result)
                s.last_pc.next = s.pc.value
                s.pc.next = s.pc.value + ILEN_BYTES

    def line_trace(s):
        return str(s.pc)
