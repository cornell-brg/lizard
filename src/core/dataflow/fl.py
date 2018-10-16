from msg.data import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import *
from util.freelist.fl import FreeListFL


class PregState(BitStructDefinition):
    def __init__(s):
        s.value = BitField(XLEN)
        s.ready = BitField(1)
        s.areg = BitField(REG_SPEC_LEN)


class DataFlowUnitFL(Model):
    def __init__(s):
        s.free_regs = FreeListFL(REG_TAG_COUNT)
        s.rename_table = [Bits(REG_TAG_LEN) for _ in range(REG_COUNT)]
        s.preg_file = [PregState() for _ in range(REG_TAG_COUNT)]
        s.areg_file = [Bits(REG_TAG_LEN) for _ in range(REG_COUNT)]

        s.mngr2proc = InValRdyBundle(Bits(XLEN))
        s.proc2mngr = OutValRdyBundle(Bits(XLEN))

        s.mngr2proc_q = InValRdyQueueAdapterFL(s.mngr2proc)
        s.proc2mngr_q = OutValRdyQueueAdapterFL(s.proc2mngr)

    def fl_reset(s):
        s.free_regs.fl_reset()
        for areg in range(REG_COUNT):
            tag = s.get_dst(areg).tag
            s.write_tag(tag, 0)
            s.commit_tag(tag, True)
        
        s.csr_file = {}


    def get_src(s, areg):
        resp = GetSrcResponse()
        resp.tag = s.rename_table[areg]
        resp.ready = s.preg_file[resp.tag].ready
        return resp

    def get_dst(s, areg):
        resp = GetDstResponse()
        preg = s.free_regs.alloc()
        if not preg:
            resp.success = 0
        else:
            s.rename_table[areg] = preg
            resp.success = 1
            resp.tag = preg
            preg_entry = s.preg_file[preg]
            preg_entry.ready = 0
            preg_entry.areg = areg
        return resp

    def read_tag(s, tag):
        resp = ReadTagResponse()
        preg = s.preg_file[tag]
        resp.ready = preg.ready
        resp.value = preg.value
        return resp

    def write_tag(s, tag, value):
        preg = s.preg_file[tag]
        preg.value = value
        preg.ready = 1

    def commit_tag(s, tag, initial=False):
        preg = s.preg_file[tag]
        if not initial:
            # Free the old one
            s.free_regs.free(s.areg_file[preg.areg])
        s.areg_file[preg.areg] = tag

    def read_csr(s, csr_num):
        if csr_num == CsrRegisters.mngr2proc:
            return s.mngr2proc_q.popleft()
        else:
            return s.csr_file.get(int(csr_num), Bits(XLEN, 0))

    def write_csr(s, csr_num, value):
        if csr_num == CsrRegisters.proc2mngr:
            s.proc2mngr_q.append(value)
        else:
            s.csr_file[int(csr_num)] = value

    def line_trace(s):
        return "<dataflowfl>"
