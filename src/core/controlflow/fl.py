from pymtl import *
from msg.data import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import *


class InstrState(BitStructDefinition):
    def __init__(s):
        s.succesor_pc = BitField(XLEN)
        s.valid = BitField(1)
        s.in_flight = BitField(1)


class ControlFlowUnitFL(Model):
    def __init__(s):
        s.seq = Bits(INST_TAG_LEN)
        s.head = Bits(INST_TAG_LEN)
        s.epoch = Bits(INST_TAG_LEN)
        s.in_flight = {}
        s.epoch_start = Bits(XLEN)

    def fl_reset(s):
        s.seq = 0
        s.head = 0
        s.epoch = 0
        s.in_flight = {}
        s.epoch_start = RESET_VECTOR

    def get_epoch_start(s, request):
        resp = GetEpochStartRespose()
        resp.current_epoch = s.epoch
        # Only a valid register if issued under a consistent epoch
        resp.valid = (request.epoch == s.epoch)
        if resp.valid:
            resp.pc = s.epoch_start
        return resp

    def register(s, request):
        resp = RegisterInstrResponse()
        resp.current_epoch = s.epoch
        # Only a valid register if issued under a consistent epoch
        resp.valid = (request.epoch == s.epoch)
        if resp.valid:
            resp.tag = s.seq
            s.seq += 1
            state = InstrState()
            state.succesor_pc = request.succesor_pc
            state.valid = 1
            state.in_flight = 1
            s.in_flight[resp.tag] = state
        return resp

    def request_redirect(s, request):
        if s.in_flight[request.source_tag] == request.target_pc:
            return

        if not s.in_flight[request.source_tag].valid:
            return

        # invalidate all later instructions
        for tag, state in s.in_flight.iteritems():
            if tag > request.tag:
                state.valid = 0

        # set a new epoch
        # all new instructions must fall sequentially "into the shadow"
        # of this one
        s.epoch = request.tag

    def tag_valid(s, request):
        return s.in_flight[request.tag].valid

    def retire(s, request):
        s.in_flight[request.tag].in_flight = 0

        while s.in_flight[s.head].in_flight == 0:
            del s.in_flight[s.head]
            s.head += 1
