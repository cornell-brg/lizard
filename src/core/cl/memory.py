from pymtl import *
from msg.mem import MemMsg8B
from msg.control import *
from msg.decode import *
from msg.issue import *
from msg.execute import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from config.general import *


# The memory execute pipe
class MemoryUnitCL( Model ):

  def __init__( s, dataflow, controlflow, memoryflow ):
    s.issued_q = InValRdyCLPort( IssuePacket() )
    s.result_q = OutValRdyCLPort( ExecutePacket() )

    s.dataflow = dataflow
    s.controlflow = controlflow
    s.memoryflow = memoryflow

    s.in_flight = Wire( 1 )
    s.current = None

  def xtick( s ):
    if s.reset:
      s.in_flight.next = 0

    if s.in_flight:
      # can't do anything until response comes back
      if not s.memoryflow.response_ready():
        return

      resp = s.memoryflow.await_response()

      result = ExecutePacket()
      copy_common_bundle( s.current, result )
      result.opcode = s.current.opcode
      copy_field_valid_pair( s.current, result, 'rd' )

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
    if s.result_q.full() or s.memoryflow.busy() or s.issued_q.empty():
      return
    s.current = s.issued_q.deq()

    # verify instruction still alive
    creq = TagValidRequest()
    creq.tag = s.current.tag
    cresp = s.controlflow.tag_valid( creq )
    if not cresp.valid:
      s.current.status = PacketStatus.SQUASHED

    if s.current.status != PacketStatus.ALIVE:
      result = ExecutePacket()
      copy_common_bundle( s.current, result )
      result.opcode = s.current.opcode
      copy_field_valid_pair( s.current, result, 'rd' )
      s.result_q.enq( s.work )
      return

    # Memory message length is number of bytes, with 0 = all (overlow)
    addr = s.current.rs1 + sext( s.current.imm, XLEN )
    byte_len = Bits(
        MemMsg8B.req.len.nbits, 2**int( s.current.funct3[ 0:2 ] ), trunc=True )
    if s.current.opcode == Opcode.LOAD:
      req = MemMsg8B.req.mk_rd( 0, addr, byte_len )
      s.memoryflow.stage( req )
      # Loads we dispatch now; they have no side effects in the event of a squash
      s.memoryflow.submit()
      # Only need to wait on a response for a load
      # Once a store has been staged, we are good
      s.in_flight.next = 1
    else:
      req = MemMsg8B.req.mk_wr( 0, addr, byte_len, s.current.rs2 )
      s.memoryflow.stage( req )

      # Once we stage we are done, so send to next stage
      result = ExecutePacket()
      copy_common_bundle( s.current, result )
      result.opcode = s.current.opcode
      copy_field_valid_pair( s.current, result, 'rd' )

      s.result_q.enq( result )

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.result_q.msg().tag ),
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.result_q.msg().inst ),
            s.result_q.msg().rd_valid,
            s.result_q.msg().rd ),
        "res: {}".format( s.result_q.msg().result ),
    ] ).validate( s.result_q.val() )
