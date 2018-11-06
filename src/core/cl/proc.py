from pymtl import *
from msg.mem import MemMsg8B
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort, cl_connect
from config.general import *
from core.cl.fetch import FetchUnitCL
from core.cl.decode import DecodeUnitCL
from core.cl.issue import IssueUnitCL
from core.cl.execute import ExecuteUnitCL
from core.cl.csrr import CSRRUnitCL
from core.cl.memory import MemoryUnitCL
from core.cl.writeback import WritebackUnitCL
from core.cl.commit import CommitUnitCL
from core.cl.dataflow import DataFlowManagerCL
from core.cl.controlflow import ControlFlowManagerCL
from core.cl.memoryflow import MemoryFlowManagerCL
from util import line_block
from util.line_block import Divider


class ProcCL( Model ):

  def __init__( s ):
    s.imem_req = OutValRdyCLPort( MemMsg8B.req )
    s.imem_resp = InValRdyCLPort( MemMsg8B.resp )

    s.dmem_req = OutValRdyCLPort( MemMsg8B.req )
    s.dmem_resp = InValRdyCLPort( MemMsg8B.resp )

    s.mngr2proc = InValRdyBundle( Bits( XLEN ) )
    s.proc2mngr = OutValRdyBundle( Bits( XLEN ) )

    s.stats_en = Bits( 1, 0 )

    s.dataflow = DataFlowManagerCL()
    s.controlflow = ControlFlowManagerCL( s.dataflow )
    s.memoryflow = MemoryFlowManagerCL()
    s.fetch = FetchUnitCL( s.controlflow )
    s.decode = DecodeUnitCL( s.controlflow )
    s.issue = IssueUnitCL( s.dataflow, s.controlflow )
    s.execute = ExecuteUnitCL( s.dataflow, s.controlflow )
    s.memory = MemoryUnitCL( s.dataflow, s.controlflow, s.memoryflow )
    s.csrr = CSRRUnitCL( s.dataflow, s.controlflow )
    s.writeback = WritebackUnitCL( s.dataflow, s.controlflow, s.memoryflow )
    s.commit = CommitUnitCL( s.dataflow, s.controlflow, s.memoryflow )

    s.connect( s.mngr2proc, s.dataflow.mngr2proc )
    s.connect( s.proc2mngr, s.dataflow.proc2mngr )

    cl_connect( s.imem_req, s.fetch.req_q )
    cl_connect( s.imem_resp, s.fetch.resp_q )
    cl_connect( s.dmem_req, s.memoryflow.mem_req )
    cl_connect( s.dmem_resp, s.memoryflow.mem_resp )

    cl_connect( s.fetch.instrs_q, s.decode.instr_q )
    cl_connect( s.decode.decoded_q, s.issue.decoded_q )
    cl_connect( s.issue.execute_q, s.execute.issued_q )
    cl_connect( s.issue.memory_q, s.memory.issued_q )
    cl_connect( s.issue.csrr_q, s.csrr.issued_q )
    cl_connect( s.execute.result_q, s.writeback.execute_q )
    cl_connect( s.memory.result_q, s.writeback.memory_q )
    cl_connect( s.csrr.result_q, s.writeback.csrr_q )
    cl_connect( s.writeback.result_out_q, s.commit.result_in_q )

  def xtick( s ):
    s.dataflow.xtick()
    s.controlflow.xtick()
    s.memoryflow.xtick()

    s.commit.xtick()
    s.writeback.xtick()
    s.execute.xtick()
    s.memory.xtick()
    s.csrr.xtick()
    s.issue.xtick()
    s.decode.xtick()
    s.fetch.xtick()

  def line_trace( s ):
    return line_block.join([
        s.fetch.line_trace(),
        Divider( ' | ' ),
        s.decode.line_trace(),
        Divider( ' | ' ),
        s.issue.line_trace(),
        Divider( ' | ' ),
        s.execute.line_trace(),
        Divider( ' | ' ),
        s.writeback.line_trace(),
        Divider( ' | ' ),
        s.commit.line_trace()
    ] )
