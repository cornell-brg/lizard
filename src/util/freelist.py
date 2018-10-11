from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from bitutil import clog2


class AllocRequest(BitStructDefinition):
    def __init__(s):
        pass

class AllocResponse(BitStructDefinition):
    def __init__(s, nbits):
        s.slot = BitField(nbits)

class FreeRequest(BitStructDefinition):
    def __init__(s, nbits):
        s.slot = BitField(nbits)

class FreeResponse(BitStructDefinition):
    def __int__(s):
        pass


class FreeListFL(Model):
    def __init__(s, nslots):

        nbits = clog2(nslots)
        s.AllocRequest = AllocRequest()
        s.AllocResponse = AllocResponse(nbits)
        s.FreeRequest = FreeRequest(nbits)
        s.FreeResponse = FreeResponse()

        s.alloc_request = InValRdyBundle(s.AllocRequest())
        s.alloc_response = OutValRdyBundle(s.AllocResponse())

        s.free_request = InValRdyBundle(s.FreeRequest())
        s.free_response = InValRdyBundle(s.FreeResponse())

        # Adapters
        s.decoded_q = InValRdyQueueAdapterFL(s.decoded)
        s.response_q = OutValRdyQueueAdapterFL(s.response)

        s.reg_file = [Bits(XLEN) for x in range(REG_COUNT)]

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
