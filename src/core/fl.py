from pymtl import *
from msg import MemMsg4B
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import *
from core.dataflow.fl import DataFlowUnitFL
from core.controlflow.fl import ControlFlowUnitFL
from core.fetch.fl import FetchFL
from core.dispatch.fl import DispatchFL
from core.issue.fl import IssueFL
from core.functional.fl import FunctionalFL
from core.result.fl import ResultFL
from core.commit.fl import CommitFL
from util import line_block
from util.line_block import Divider


class CoreFL( Model ):

  def __init__( s ):
    s.mem_req = OutValRdyBundle( MemMsg4B.req )
    s.mem_resp = InValRdyBundle( MemMsg4B.resp )

    s.mngr2proc = InValRdyBundle( Bits( XLEN ) )
    s.proc2mngr = OutValRdyBundle( Bits( XLEN ) )

    s.stats_en = Bits( 1, 0 )

    s.dataflow = DataFlowUnitFL()
    s.controlflow = ControlFlowUnitFL( s.dataflow )
    s.fetch = FetchFL( s.controlflow )
    s.dispatch = DispatchFL( s.controlflow )
    s.issue = IssueFL( s.dataflow, s.controlflow )
    s.functional = FunctionalFL( s.dataflow, s.controlflow )
    s.result = ResultFL( s.dataflow, s.controlflow )
    s.commit = CommitFL( s.dataflow, s.controlflow )

    s.connect( s.mngr2proc, s.dataflow.mngr2proc )
    s.connect( s.proc2mngr, s.dataflow.proc2mngr )

    s.connect( s.mem_req, s.fetch.mem_req )
    s.connect( s.mem_resp, s.fetch.mem_resp )
    s.connect( s.fetch.instrs, s.dispatch.instr )
    s.connect( s.dispatch.decoded, s.issue.decoded )
    s.connect( s.issue.issued, s.functional.issued )
    s.connect( s.functional.result, s.result.result_in )
    s.connect( s.result.result_out, s.commit.result_in )

    @s.tick_fl
    def tick():
      if s.reset:
        s.dataflow.fl_reset()
        s.controlflow.fl_reset()

  def line_trace( s ):
    return line_block.join([
        'F: ',
        s.fetch.line_trace(),
        Divider( ' | ' ), 'D: ',
        s.dispatch.line_trace(),
        Divider( ' | ' ), 'I: ',
        s.issue.line_trace(),
        Divider( ' | ' ), 'E: ',
        s.functional.line_trace(),
        Divider( ' | ' ), 'R: ',
        s.result.line_trace(),
        Divider( ' | ' ), 'C: ',
        s.commit.line_trace()
    ] )
