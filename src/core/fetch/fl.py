from pymtl import *
from msg import MemMsg4B
from msg.fetch import FetchPacket
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from pclib.cl import InValRdyQueueAdapter, OutValRdyQueueAdapter
from config.general import *
from util.line_block import LineBlock
from copy import deepcopy


class FetchFL( Model ):

  def __init__( s, controlflow ):
    s.mem_req = OutValRdyBundle( MemMsg4B.req )
    s.mem_resp = InValRdyBundle( MemMsg4B.resp )
    s.instrs = OutValRdyBundle( FetchPacket() )

    s.req_q = OutValRdyQueueAdapter( s.mem_req )
    s.resp_q = InValRdyQueueAdapter( s.mem_resp )
    # output
    s.instrs_q = UnbufferedOutValRdyQueueAdapter( s.instrs )

    s.pc = Wire( XLEN )
    s.bad = Wire( 1 )
    s.epoch = Wire( INST_TAG_LEN )
    s.in_flight = Wire( 1 )
    s.pc_in_flight = Wire( XLEN )
    s.pc_in_flight_successor = Wire( XLEN )

    s.controlflow = controlflow

  def xtick( s ):
    s.req_q.xtick()
    s.resp_q.xtick()
    s.instrs_q.xtick()

    if s.reset:
      s.bad.next = 1
      s.epoch.next = 0
      s.in_flight.next = 0
      return

    if s.instrs_q.full():
      return

    if s.bad.value:
      req = GetEpochStartRequest()
      req.epoch = s.epoch.value
      resp = s.controlflow.get_epoch_start( req )
      if resp.valid:
        s.pc.next = resp.pc
      s.epoch.next = resp.current_epoch

      # if a request is in flight drop it
      next_in_flight = s.in_flight.value
      if s.in_flight.value and not s.resp_q.empty():
        s.resp_q.deq()
        next_in_flight = 0
        s.in_flight.next = next_in_flight

      # stay bad until no more requests in flight
      s.bad.next = not resp.valid or next_in_flight
    else:
      # if we got one back
      if s.in_flight.value and not s.resp_q.empty():
        mem_resp = s.resp_q.deq()
        s.in_flight.next = 0
        out = FetchPacket()
        out.instr = mem_resp.data
        out.pc = s.pc_in_flight.value

        req = RegisterInstrRequest()
        req.succesor_pc = s.pc_in_flight_successor.value
        req.epoch = s.epoch.value
        resp = s.controlflow.register( req )
        if resp.valid:
          out.tag = resp.tag
          s.instrs_q.enq( out )
        s.epoch.next = resp.current_epoch
        s.bad.next = not resp.valid

      if not s.req_q.full() and not s.in_flight.next:
        s.req_q.enq( MemMsg4B.req.mk_rd( 0, s.pc.value, 0 ) )
        s.pc_in_flight.next = s.pc.value
        s.pc.next = s.pc.value + ILEN_BYTES
        s.pc_in_flight_successor.next = s.pc.value + ILEN_BYTES
        s.in_flight.next = 1

  def line_trace( s ):
    return LineBlock([
        'epoch: {}'.format( s.epoch ),
        'pc: {}'.format( s.instrs_q.msg().pc ),
    ] ).validate( s.instrs_q.val() )
