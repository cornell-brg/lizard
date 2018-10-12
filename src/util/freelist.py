from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from bitutil import clog2

class EmptyMessage(BitStructDefinition):
    def __init__(s):
        s.foo = BitField(1)

AllocRequest = EmptyMessage

class AllocResponse(BitStructDefinition):
    def __init__(s, nbits):
        s.slot = BitField(nbits)


class FreeRequest(BitStructDefinition):
    def __init__(s, nbits):
        s.slot = BitField(nbits)


FreeResponse = EmptyMessage


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

        s.alloc_request_q = InValRdyQueueAdapterFL(s.alloc_request)
        s.alloc_response_q = OutValRdyQueueAdapterFL(s.alloc_response)
        s.free_request_q = InValRdyQueueAdapterFL(s.free_request)
        s.free_response_q = InValRdyQueueAdapterFL(s.free_response)

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
        return "\xc2\_(\xe3)_/\xc2"
