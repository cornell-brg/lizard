from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.result import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from util.line_block import LineBlock
from copy import deepcopy


class ResultFL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.result_in = InValRdyBundle( FunctionalPacket() )
    s.result_out = OutValRdyBundle( ResultPacket() )

    s.result_in_q = UnbufferedInValRdyQueueAdapter( s.result_in )
    s.result_out_q = UnbufferedOutValRdyQueueAdapter( s.result_out )

    s.dataflow = dataflow
    s.controlflow = controlflow

  def xtick( s ):
    s.result_in_q.xtick()
    s.result_out_q.xtick()

    if s.reset:
      return

    if s.result_out_q.full():
      return

    if s.result_in_q.empty():
      s.result_in_q.assert_rdy()
      return

    p = s.result_in_q.deq()

    # verify instruction still alive
    creq = TagValidRequest()
    creq.tag = p.tag
    cresp = s.controlflow.tag_valid( creq )
    if not cresp.valid:
      # if we allocated a destination register for this instruction,
      # we must free it
      if p.rd_valid:
        s.dataflow.free_tag( p.rd )
      # retire instruction from controlflow
      creq = RetireRequest()
      creq.tag = p.tag
      s.controlflow.retire( creq )
      return

    if p.rd_valid:
      s.dataflow.write_tag( p.rd, p.result )

    out = ResultPacket()
    out.inst = p.inst
    out.rd_valid = p.rd_valid
    out.rd = p.rd
    out.result = p.result
    out.pc = p.pc
    out.tag = p.tag
    s.result_out_q.enq( out )

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.result_out_q.msg().tag ),
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.result_out_q.msg().inst ),
            s.result_out_q.msg().rd_valid,
            s.result_out_q.msg().rd ),
        "res: {}".format( s.result_out_q.msg().result ),
    ] ).validate( s.result_out_q.val() )
