from pymtl import *
from lizard.msg.mem import MemMsg8B
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from lizard.util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from lizard.util.cl.ports import InValRdyCLPort, OutValRdyCLPort, cl_connect
from lizard.config.general import *
from lizard.core.cl.fetch import FetchUnitCL
from lizard.core.cl.decode import DecodeUnitCL
from lizard.core.cl.issue import IssueUnitCL
from lizard.core.cl.execute import ExecuteUnitCL
from lizard.core.cl.muldiv import MulDivUnitCL
from lizard.core.cl.csrr import CSRRUnitCL
from lizard.core.cl.memory import MemoryUnitCL
from lizard.core.cl.writeback import WritebackUnitCL
from lizard.core.cl.commit import CommitUnitCL
from lizard.core.cl.dataflow import DataFlowManagerCL
from lizard.core.cl.controlflow import ControlFlowManagerCL
from lizard.core.cl.memoryflow import MemoryFlowManagerCL
from lizard.util import line_block
from lizard.util.line_block import Divider


class ProcCL(Model):

  def __init__(s):
    s.imem_req = OutValRdyCLPort(MemMsg8B.req)
    s.imem_resp = InValRdyCLPort(MemMsg8B.resp)

    s.dmem_req = OutValRdyCLPort(MemMsg8B.req)
    s.dmem_resp = InValRdyCLPort(MemMsg8B.resp)

    s.mngr2proc = InValRdyBundle(Bits(XLEN))
    s.proc2mngr = OutValRdyBundle(Bits(XLEN))

    s.stats_en = Bits(1, 0)

    s.dataflow = DataFlowManagerCL()
    s.controlflow = ControlFlowManagerCL(s.dataflow)
    s.memoryflow = MemoryFlowManagerCL()
    s.fetch = FetchUnitCL(s.controlflow)
    s.decode = DecodeUnitCL(s.controlflow)
    s.issue = IssueUnitCL(s.dataflow, s.controlflow)
    s.execute = ExecuteUnitCL(s.dataflow, s.controlflow)
    s.muldiv = MulDivUnitCL(s.dataflow, s.controlflow)
    s.memory = MemoryUnitCL(s.dataflow, s.controlflow, s.memoryflow)
    s.csrr = CSRRUnitCL(s.dataflow, s.controlflow)
    s.writeback = WritebackUnitCL(s.dataflow, s.controlflow, s.memoryflow)
    s.commit = CommitUnitCL(s.dataflow, s.controlflow, s.memoryflow)

    s.connect(s.mngr2proc, s.dataflow.mngr2proc)
    s.connect(s.proc2mngr, s.dataflow.proc2mngr)

    cl_connect(s.imem_req, s.fetch.req_q)
    cl_connect(s.imem_resp, s.fetch.resp_q)
    cl_connect(s.dmem_req, s.memoryflow.mem_req)
    cl_connect(s.dmem_resp, s.memoryflow.mem_resp)

    cl_connect(s.fetch.instrs_q, s.decode.instr_q)
    cl_connect(s.decode.decoded_q, s.issue.decoded_q)
    cl_connect(s.issue.execute_q, s.execute.issued_q)
    cl_connect(s.issue.muldiv_q, s.muldiv.issued_q)
    cl_connect(s.issue.memory_q, s.memory.issued_q)
    cl_connect(s.issue.csrr_q, s.csrr.issued_q)
    cl_connect(s.execute.result_q, s.writeback.execute_q)
    cl_connect(s.muldiv.result_q, s.writeback.muldiv_q)
    cl_connect(s.memory.result_q, s.writeback.memory_q)
    cl_connect(s.csrr.result_q, s.writeback.csrr_q)
    cl_connect(s.writeback.result_out_q, s.commit.result_in_q)

  def xtick(s):
    s.dataflow.xtick()
    s.controlflow.xtick()
    s.memoryflow.xtick()

    s.commit.xtick()
    s.writeback.xtick()
    s.execute.xtick()
    s.muldiv.xtick()
    s.memory.xtick()
    s.csrr.xtick()
    s.issue.xtick()
    s.decode.xtick()
    s.fetch.xtick()

  def line_trace(s):
    return line_block.join([
        s.fetch.line_trace(),
        Divider(' | '),
        s.decode.line_trace(),
        Divider(' | '),
        s.issue.line_trace(),
        Divider(' | '),
        s.execute.line_trace(),
        Divider(' | '),
        s.memory.line_trace(),
        Divider(' | '),
        s.writeback.line_trace(),
        Divider(' | '),
        s.commit.line_trace()
    ])
