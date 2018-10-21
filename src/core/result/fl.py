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

    s.out = Wire( ResultPacket() )
    s.out_valid = Wire( 1 )

  def xtick( s ):
    s.result_in_q.xtick()
    s.result_out_q.xtick()

    if s.reset:
      s.out_valid.next = 0
      return

    if s.out_valid:
      if not s.result_out_q.full():
        s.result_out_q.enq( deepcopy( s.out ) )
        s.out_valid.next = 0
      else:
        return

    if s.result_in_q.empty():
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

    s.out.next = ResultPacket()
    s.out.next.inst = p.inst
    s.out.next.rd_valid = p.rd_valid
    s.out.next.rd = p.rd
    s.out.next.result = p.result
    s.out.next.pc = p.pc
    s.out.next.tag = p.tag
    s.out_valid.next = 1

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.out.tag ), "{: <8} rd({}): {}".format(
            RV64Inst.name( s.out.inst ), s.out.rd_valid, s.out.rd ),
        "res: {}".format( s.out.result )
    ] ).validate( s.out_valid )
