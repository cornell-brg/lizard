from pymtl import *
from msg.decode import *
from msg.data import *
from msg.issue import *
from msg.execute import *
from msg.writeback import *
from msg.control import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from util.cl.port_groups import InValRdyCLPortGroup
from util.line_block import LineBlock
from copy import deepcopy


class WritebackUnitCL( Model ):

  def __init__( s, dataflow, controlflow, memoryflow ):
    s.execute_q = InValRdyCLPort( ExecutePacket() )
    s.muldiv_q = InValRdyCLPort( ExecutePacket() )
    s.memory_q = InValRdyCLPort( ExecutePacket() )
    s.csrr_q = InValRdyCLPort( ExecutePacket() )
    s.in_ports = [ s.csrr_q, s.memory_q, s.muldiv_q, s.execute_q ]
    s.result_in_q = InValRdyCLPortGroup( s.in_ports )
    s.result_out_q = OutValRdyCLPort( WritebackPacket() )

    s.dataflow = dataflow
    s.controlflow = controlflow
    s.memoryflow = memoryflow

  def xtick( s ):
    if s.reset:
      return

    if s.result_out_q.full():
      return

    if s.result_in_q.empty():
      return

    # drop idx, don't care which port it came out of
    p, _ = s.result_in_q.deq()

    out = WritebackPacket()
    copy_common_bundle( p, out )
    out.opcode = p.opcode
    copy_field_valid_pair( p, out, 'rd' )
    out.result = p.result

    if out.status != PacketStatus.ALIVE:
      s.result_out_q.enq( out )
      return

    if p.rd_valid:
      s.dataflow.write_tag( p.rd, p.result )

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
