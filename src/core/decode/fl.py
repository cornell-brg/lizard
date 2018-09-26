#=========================================================================
# Decode FL Model
#=========================================================================

from pymtl import *
from msg import MemMsg4B
from msg.fetch import FetchPacket
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR


class DecodeFL(Model):
    def __init__(s):
        # dpath
        s.instr = OutValRdyBundle(FetchPacket())
        s.instr_q = InValRdyQueueAdapterFL(s.instr)

        s.pc = Wire(Bits(XLEN))

        @s.tick_fl
        def tick():
            if s.reset:
                pass
            else:
                inst = s.instr_q.popleft()
                # Decode it



    def line_trace(s):
        return str(s.pc)
