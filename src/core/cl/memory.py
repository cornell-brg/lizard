from pymtl import *
from msg.mem import MemMsg8B
from msg.control import *
from msg.decode import *
from msg.issue import *
from msg.execute import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from config.general import *


class MemoryUnitCL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.issued_q = InValRdyCLPort( IssuePacket() )
    s.result_q = OutValRdyCLPort( ExecutePacket() )

    s.mem_req_q = OutValRdyCLPort( MemMsg8B.req )
    s.mem_resp_q = InValRdyCLPort( MemMsg8B.resp )

    s.dataflow = dataflow
    s.controlflow = controlflow

    s.in_flight = Wire( 1 )
    s.current = None

  def xtick( s ):
    if s.reset:
      s.in_flight.next = 0

    if s.in_flight:
      # can't do anything until response comes back
      if s.mem_resp_q.empty():
        return

      resp = s.mem_resp_q.deq()

      result = ExecutePacket()
      result.inst = s.current.inst
      result.rd_valid = s.current.rd_valid
      result.rd = s.current.rd
      result.pc = s.current.pc
      result.tag = s.current.tag

      if s.current.opcode == Opcode.LOAD:
        if s.current.funct3[ 2 ] == 0:
          extender = sext
        else:
          extender = zext
        data_len = 8 * 2**int( s.current.funct3[ 0:2 ] )
        data = extender( Bits( data_len, int( resp.data ), trunc=True ), XLEN )
        result.result = data

      s.result_q.enq( result )
      s.in_flight.next = 0

    # Nothing left in flight now, try to issue another one
    if s.result_q.full() or s.mem_req_q.full() or s.issued_q.empty():
      return
    s.current = s.issued_q.deq()

    # verify instruction still alive
    creq = TagValidRequest()
    creq.tag = s.current.tag
    cresp = s.controlflow.tag_valid( creq )
    if not cresp.valid:
      # if we allocated a destination register for this instruction,
      # we must free it
      if s.current.rd_valid:
        s.dataflow.free_tag( s.current.rd )
      # retire instruction from controlflow
      creq = RetireRequest()
      creq.tag = s.current.tag
      s.controlflow.retire( creq )
      return

    # Memory message length is number of bytes, with 0 = all (overlow)
    addr = s.current.rs1 + sext( s.current.imm, XLEN )
    byte_len = Bits(
        MemMsg8B.req.len.nbits, 2**int( s.current.funct3[ 0:2 ] ), trunc=True )
    if s.current.opcode == Opcode.LOAD:
      req = MemMsg8B.req.mk_rd( 0, addr, byte_len )
    else:
      req = MemMsg8B.req.mk_wr( 0, addr, byte_len, s.current.rs2 )
    s.mem_req_q.enq( req )
    s.in_flight.next = 1

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.result_q.msg().tag ),
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.result_q.msg().inst ),
            s.result_q.msg().rd_valid,
            s.result_q.msg().rd ),
        "res: {}".format( s.result_q.msg().result ),
    ] ).validate( s.result_q.val() )
