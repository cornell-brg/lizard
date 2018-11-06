from pymtl import *
from msg.decode import *
from msg.data import *
from msg.issue import *
from msg.execute import *
from msg.control import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from util.line_block import LineBlock
from copy import deepcopy


class CSRRUnitCL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.issued_q = InValRdyCLPort( IssuePacket() )
    s.result_q = OutValRdyCLPort( ExecutePacket() )

    s.dataflow = dataflow
    s.controlflow = controlflow

    s.done = Wire( 1 )

  def xtick( s ):
    if s.reset:
      s.done.next = 1
      return

    if s.result_q.full():
      return

    if s.done:
      if s.issued_q.empty():
        return
      s.current = s.issued_q.deq()
      s.work = ExecutePacket()
      copy_common_bundle( s.current, s.work )
      s.work.opcode = s.current.opcode
      copy_field_valid_pair( s.current, s.work, 'rd' )


    # verify instruction still alive
    # TODO fix this
    creq = TagValidRequest()
    creq.tag = s.current.tag
    cresp = s.controlflow.tag_valid( creq )
    if not cresp.valid:
      s.work.status = PacketStatus.SQUASHED

    if s.work.status != PacketStatus.ALIVE:
      s.done.next = 1
      s.result_q.enq( s.work )
      return

    s.done.next = 1 # Assume everythig works

    if s.current.inst == RV64Inst.CSRRW or s.current.inst == RV64Inst.CSRRWI:
      temp, worked = s.dataflow.read_csr( s.current.csr )
      if not worked:
        s.done.next = 0
      else:
        s.work.result = temp
        if s.current.inst == RV64Inst.CSRRWI:
          value = zext( s.current.imm, XLEN )
        else:
          value = s.current.rs1
        s.dataflow.write_csr( s.current.csr, value )
    elif s.current.inst == RV64Inst.CSRRS or s.current.inst == RV64Inst.CSRRSI:
      temp, worked = s.dataflow.read_csr( s.current.csr )
      if not worked:
        s.done.next = 0
      else:
        s.work.result = temp
        if s.current.inst == RV64Inst.CSRRSI:
          value = zext( s.current.imm, XLEN )
        else:
          value = s.current.rs1
        # TODO: not quite right because we should attempt to set
        # if the value of rs1 is zero but rs1 is not x0
        if value != 0:
          s.dataflow.write_csr( s.current.csr, s.work.result | value )
    else:
      raise NotImplementedError( 'Not implemented so sad: ' +
                                 RV64Inst.name( s.current.inst ) )

    # Did we finish an instruction this cycle?
    if s.done.next:
      # Output the finished instruction
      s.result_q.enq( s.work )



  def line_trace( s ):
    return LineBlock([
        "{}".format( s.result_q.msg().tag ),
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.result_q.msg().inst ),
            s.result_q.msg().rd_valid,
            s.result_q.msg().rd ),
        "res: {}".format( s.result_q.msg().result ),
    ] ).validate( s.result_q.val() )
