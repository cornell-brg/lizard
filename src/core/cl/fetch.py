from pymtl import *
from msg.packet_common import *
from msg.mem import MemMsg8B
from msg.fetch import FetchPacket
from msg.control import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from config.general import *
from util.line_block import LineBlock
from copy import deepcopy


class FetchUnitCL( Model ):

  def __init__( s, controlflow ):
    s.req_q = OutValRdyCLPort( MemMsg8B.req )
    s.resp_q = InValRdyCLPort( MemMsg8B.resp )
    s.instrs_q = OutValRdyCLPort( FetchPacket() )

    s.in_flight = Wire( 1 )
    s.drop_mem = Wire( 1 )

    s.pc = Wire( XLEN )
    s.pc_in_flight = Wire( XLEN )


    s.controlflow = controlflow

  def xtick( s ):
    if s.reset:
      s.drop_mem = False

    # Check if the controlflow is redirecting the front end
    redirected = s.controlflow.check_redirect()
    if redirected.valid: # Squash everything
      # drop any mem responses
      if (not s.resp_q.empty()):
        s.resp_q.deq()
      else:
        s.drop_mem = s.in_flight
      # Redirect PC
      s.pc.next = redirected.target
      return

    # Drop unit
    if s.drop_mem and not s.resp_q.empty():
      s.resp_q.deq()
      drop_mem = False
      s.in_flight = False


    # We got a memresp
    if not s.resp_q.empty() and not s.instrs_q.full():
      mem_resp = s.resp_q.deq()
      out = FetchPacket()
      out.status = PacketStatus.ALIVE
      out.instr = mem_resp.data
      out.pc = s.pc_in_flight
      out.pc_next = s.pc
      s.instrs_q.enq( out )

      s.in_flight = False


    if not s.in_flight: # We can send next request
      s.req_q.enq( MemMsg8B.req.mk_rd( 0, s.pc, ILEN_BYTES ) )
      s.in_flight = True
      s.pc_in_flight.next = s.pc
      #TODO insert btb here, so easy!
      s.pc.next = s.pc + ILEN_BYTES


  def line_trace( s ):
    return LineBlock([
        'epoch: {}'.format( 0 ),
        'pc: {}'.format( s.instrs_q.msg().pc ),
    ] ).validate( s.instrs_q.val() )
