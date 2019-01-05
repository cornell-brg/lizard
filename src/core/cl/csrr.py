from pymtl import *
from msg.datapath import *
from msg.data import *
from msg.control import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from util.line_block import LineBlock
from copy import deepcopy


# The CSRR execute pipe
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
      copy_issue_execute( s.current, s.work )

    # verify instruction still alive
    if s.work.status != PacketStatus.ALIVE:
      s.done.next = 1
      s.result_q.enq( s.work )
      return

    s.done.next = 1  # Assume finishes this cycle

    if s.current.instr_d == RV64Inst.CSRRW or s.current.instr_d == RV64Inst.CSRRWI:
      temp, worked = s.dataflow.read_csr( s.current.csr )
      if not worked:
        s.done.next = 0
      else:
        s.work.result = temp
        if s.current.instr_d == RV64Inst.CSRRWI:
          value = zext( s.current.imm, XLEN )
        else:
          value = s.current.rs1_value
        s.dataflow.write_csr( s.current.csr, value )
    elif s.current.instr_d == RV64Inst.CSRRS or s.current.instr_d == RV64Inst.CSRRSI:
      temp, worked = s.dataflow.read_csr( s.current.csr )
      if not worked:
        s.done.next = 0
      else:
        s.work.result = temp
        if s.current.instr_d == RV64Inst.CSRRSI:
          value = zext( s.current.imm, XLEN )
        else:
          value = s.current.rs1_value
        # TODO: not quite right because we should attempt to set
        # if the value of rs1 is zero but rs1 is not x0
        if value != 0:
          s.dataflow.write_csr( s.current.csr, s.work.result | value )
    elif s.current.instr_d == RV64Inst.ECALL:
      s.work.status = PacketStatus.EXCEPTION_TRIGGERED
      s.work.mcause = ExceptionCode.ENVIRONMENT_CALL_FROM_U
    elif s.current.instr_d == RV64Inst.EBREAK:
      s.work.status = PacketStatus.EXCEPTION_TRIGGERED
      s.work.mcause = ExceptionCode.BREAKPOINT
    else:
      raise NotImplementedError( 'Not implemented so sad: ' +
                                 RV64Inst.name( s.current.instr_d ) )

    # Did we finish an instruction this cycle?
    if s.done.next:
      # Output the finished instruction
      s.result_q.enq( s.work )

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.result_q.msg().tag ),
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.result_q.msg().instr_d ),
            s.result_q.msg().rd_valid,
            s.result_q.msg().rd ),
        "res: {}".format( s.result_q.msg().result ),
    ] ).validate( s.result_q.val() )
