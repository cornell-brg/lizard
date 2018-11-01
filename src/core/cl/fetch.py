from pymtl import *
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

    s.pc = Wire( XLEN )
    s.epoch = Wire( INST_TAG_LEN )

    s.pc_in_flight = Wire( XLEN )
    s.epoch_in_flight = Wire( INST_TAG_LEN )
    s.pc_in_flight_successor = Wire( XLEN )

    s.controlflow = controlflow

  def xtick( s ):
    if s.reset:
      s.epoch.next = -1
      s.in_flight.next = 0
      return

    if s.instrs_q.full():
      return

    advance = not ( s.in_flight and s.resp_q.empty() )

    # if we got one back
    if not s.resp_q.empty():
      mem_resp = s.resp_q.deq()
      out = FetchPacket()
      out.valid = 1
      out.instr = mem_resp.data
      out.pc = s.pc_in_flight

      req = RegisterInstrRequest()
      req.succesor_pc = s.pc_in_flight_successor
      req.epoch = s.epoch_in_flight
      resp = s.controlflow.register( req )
      if resp.valid:
        out.tag = resp.tag
        s.instrs_q.enq( out )

      s.in_flight.next = 0

    if not s.req_q.full() and advance:
      # check for a redirect
      req = GetEpochStartRequest()
      req.epoch = s.epoch.value
      resp = s.controlflow.get_epoch_start( req )
      if resp.valid:
        fetch_pc = s.pc.value
      else:
        fetch_pc = resp.pc
        s.epoch.next = resp.current_epoch

      s.req_q.enq( MemMsg8B.req.mk_rd( 0, fetch_pc, ILEN_BYTES ) )
      s.pc_in_flight.next = fetch_pc
      s.epoch_in_flight = resp.current_epoch
      s.pc_in_flight_successor.next = fetch_pc + ILEN_BYTES

      #TODO insert btb here, so easy!
      s.pc.next = fetch_pc + ILEN_BYTES

      s.in_flight.next = 1

  def line_trace( s ):
    return LineBlock([
        'epoch: {}'.format( s.epoch ),
        'pc: {}'.format( s.instrs_q.msg().pc ),
    ] ).validate( s.instrs_q.val() )
