from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.result import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from util.line_block import LineBlock


class ResultFL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.result_in = InValRdyBundle( FunctionalPacket() )
    s.result_out = OutValRdyBundle( ResultPacket() )

    s.result_in_q = InValRdyQueueAdapterFL( s.result_in )
    s.result_out_q = OutValRdyQueueAdapterFL( s.result_out )

    s.dataflow = dataflow
    s.controlflow = controlflow

    s.out = ResultPacket()

    @s.tick_fl
    def tick():
      p = s.result_in_q.popleft()

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
        dataflow.write_tag( p.rd, p.result )

      s.out = ResultPacket()
      s.out.inst = p.inst
      s.out.rd_valid = p.rd_valid
      s.out.result.rd = p.rd
      s.out.result = p.result
      s.out.pc = p.pc
      s.out.tag = p.tag

      s.result_out_q.append( s.out )

  def line_trace( s ):
    return LineBlock([
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.out.inst ), s.out.rd_valid, s.out.rd ),
        "res: {}".format( s.out.result )
    ] )
