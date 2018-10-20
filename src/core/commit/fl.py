from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.result import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from util.line_block import LineBlock


class CommitFL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.result_in = InValRdyBundle( ResultPacket() )
    s.result_in_q = InValRdyQueueAdapterFL( s.result_in )

    s.dataflow = dataflow
    s.controlflow = controlflow
    s.committed = Bits( INST_TAG_LEN )

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
        s.dataflow.commit_tag( p.rd )

      # retire instruction from controlflow
      creq = RetireRequest()
      creq.tag = p.tag
      s.controlflow.retire( creq )
      s.committed = p.tag

  def line_trace( s ):
    return "{}".format( s.committed )
