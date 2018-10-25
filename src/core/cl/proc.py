from pymtl import *
from msg import MemMsg4B
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort, cl_connect
from config.general import *
from core.cl.fetch import FetchUnitCL
from core.cl.decode import DecodeUnitCL
from core.cl.issue import IssueUnitCL
from core.cl.execute import ExecuteUnitCL
from core.cl.writeback import WritebackUnitCL
from core.cl.commit import CommitUnitCL
from core.cl.dataflow import DataFlowManagerCL
from core.cl.controlflow import ControlFlowManagerCL
from util import line_block
from util.line_block import Divider


class ProcCL( Model ):

  def __init__( s ):
    s.mem_req = OutValRdyCLPort( MemMsg4B.req )
    s.mem_resp = InValRdyCLPort( MemMsg4B.resp )

    s.mngr2proc = InValRdyBundle( Bits( XLEN ) )
    s.proc2mngr = OutValRdyBundle( Bits( XLEN ) )

    s.stats_en = Bits( 1, 0 )

    s.dataflow = DataFlowManagerCL()
    s.controlflow = ControlFlowManagerCL( s.dataflow )
    s.fetch = FetchUnitCL( s.controlflow )
    s.decode = DecodeUnitCL( s.controlflow )
    s.issue = IssueUnitCL( s.dataflow, s.controlflow )
    s.functional = ExecuteUnitCL( s.dataflow, s.controlflow )
    s.writeback = WritebackUnitCL( s.dataflow, s.controlflow )
    s.commit = CommitUnitCL( s.dataflow, s.controlflow )

    s.connect( s.mngr2proc, s.dataflow.mngr2proc )
    s.connect( s.proc2mngr, s.dataflow.proc2mngr )

    cl_connect( s.mem_req, s.fetch.req_q )
    cl_connect( s.mem_resp, s.fetch.resp_q )
    cl_connect( s.fetch.instrs_q, s.decode.instr_q )
    cl_connect( s.decode.decoded_q, s.issue.decoded_q )
    cl_connect( s.issue.issued_q, s.functional.issued_q )
    cl_connect( s.functional.result_q, s.writeback.result_in_q )
    cl_connect( s.writeback.result_out_q, s.commit.result_in_q )

  def xtick( s ):
    if s.reset:
      s.dataflow.fl_reset()
      s.controlflow.fl_reset()
    s.dataflow.xtick()
    s.commit.xtick()
    s.writeback.xtick()
    s.functional.xtick()
    s.issue.xtick()
    s.decode.xtick()
    s.fetch.xtick()

  def line_trace( s ):
    return line_block.join([
        'F: ',
        s.fetch.line_trace(),
        Divider( ' | ' ),
        s.decode.line_trace(),
        Divider( ' | ' ),
        s.issue.line_trace(),
        Divider( ' | ' ),
        s.functional.line_trace(),
        Divider( ' | ' ),
        s.writeback.line_trace(),
        Divider( ' | ' ),
        s.commit.line_trace()
    ] )
