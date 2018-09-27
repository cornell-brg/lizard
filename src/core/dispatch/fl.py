#=========================================================================
# Decode FL Model
#=========================================================================

from pymtl import *
from msg import MemMsg4B
from msg.fetch import FetchPacket
from msg.decode import DecodePacket
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR


class DispatchFL(Model):
    def __init__(s):
        # input
        s.instr = InValRdyBundle(FetchPacket())
        s.instr_q = InValRdyQueueAdapterFL(s.instr)

        s.pc = Wire(Bits(XLEN))
        s.decode_q = OutValRdyQueueAdapterFL(DecodePacket())

        @s.tick_fl
        def tick():
            if s.reset:
                pass
            else:
                inst = s.instr_q.popleft()
                # Decode it and create packet
                result = DecodePacket()





    def line_trace(s):
        return str(s.pc)
