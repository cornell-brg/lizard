from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.cl import InValRdyQueueAdapter, OutValRdyQueueAdapter
from util.line_block import LineBlock
from copy import deepcopy


class FunctionalFL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.issued = InValRdyBundle( IssuePacket() )
    s.result = OutValRdyBundle( FunctionalPacket() )

    s.issued_q = InValRdyQueueAdapter( s.issued )
    s.result_q = OutValRdyQueueAdapter( s.result )

    s.dataflow = dataflow
    s.controlflow = controlflow

    s.out = Wire( FunctionalPacket() )
    s.out_valid = Wire( 1 )
    s.done = Wire( 1 )

  def xtick( s ):
    s.issued_q.xtick()
    s.result_q.xtick()

    if s.reset:
      s.out_valid.next = 0
      s.done.next = 1
      return

    if s.out_valid:
      if not s.result_q.full():
        s.result_q.enq( deepcopy( s.out ) )
        s.out_valid.next = 0
      else:
        return

    if s.done:
      if s.issued_q.empty():
        return
      s.p = s.issued_q.deq()

    # verify instruction still alive
    creq = TagValidRequest()
    creq.tag = s.p.tag
    cresp = s.controlflow.tag_valid( creq )
    if not cresp.valid:
      # if we allocated a destination register for this instruction,
      # we must free it
      if s.p.rd_valid:
        s.dataflow.free_tag( s.p.rd )
      # retire instruction from controlflow
      creq = RetireRequest()
      creq.tag = s.p.tag
      s.controlflow.retire( creq )
      return

    s.out.next = FunctionalPacket()
    s.out.next.inst = s.p.inst
    s.out.next.rd_valid = s.p.rd_valid
    s.out.next.rd = s.p.rd

    if s.p.inst == RV64Inst.ADDI:
      s.out.next.result = s.p.rs1 + sext( s.p.imm, XLEN )
    elif s.p.inst == RV64Inst.SLTI:
      if s.p.rs1.int() < s.p.imm.int():
        s.out.next.result = 1
      else:
        s.out.next.result = 0
    elif s.p.inst == RV64Inst.SLTIU:
      if s.p.rs1.uint() < s.p.imm.uint():
        s.out.next.result = 1
      else:
        s.out.next.result = 0
    elif s.p.inst == RV64Inst.XORI:
      s.out.next.result = s.p.rs1 ^ sext( s.p.imm, XLEN )
    elif s.p.inst == RV64Inst.ORI:
      s.out.next.result = s.p.rs1 | sext( s.p.imm, XLEN )
    elif s.p.inst == RV64Inst.ANDI:
      s.out.next.result = s.p.rs1 & sext( s.p.imm, XLEN )
    elif s.p.inst == RV64Inst.SLLI:
      s.out.next.result = s.p.rs1 << s.p.imm
    elif s.p.inst == RV64Inst.SRLI:
      s.out.next.result = Bits(
          XLEN, s.p.rs1.uint() >> s.p.imm.uint(), trunc=True )
    elif s.p.inst == RV64Inst.SRAI:
      s.out.next.result = Bits(
          XLEN, s.p.rs1.int() >> s.p.imm.uint(), trunc=True )
    # Register register insts
    elif s.p.inst == RV64Inst.ADD:
      s.out.result = s.p.rs1 + s.p.rs2
    elif s.p.inst == RV64Inst.SUB:
      s.out.result = s.p.rs1 - s.p.rs2
    elif s.p.inst == RV64Inst.SLL:
      s.out.result = s.p.rs1 << s.p.rs2
    elif s.p.inst == RV64Inst.SRL:
      s.out.result = s.p.rs1 >> s.p.rs2
    elif s.p.inst == RV64Inst.SLT:
      s.out.result = int(s.p.rs1.int() < s.p.rs2.int())
    elif s.p.inst == RV64Inst.SLTU:
      s.out.result = int(s.p.rs1.uint() < s.p.rs2.uint())
    elif s.p.inst == RV64Inst.XOR:
      s.out.result = s.p.rs1 ^ s.p.rs2
    elif s.p.inst == RV64Inst.OR:
      s.out.result = s.p.rs1 | s.p.rs2
    elif s.p.inst == RV64Inst.AND:
      s.out.result = s.p.rs1 & s.p.rs2
    elif s.p.inst == RV64Inst.SRA:
      s.out.result = Bits( XLEN, s.p.rs1.int() >> s.p.rs2.uint(), trunc=True )
    elif s.p.is_branch:
      taken = False
      base = s.p.pc
      if s.p.inst == RV64Inst.BEQ:
        taken = s.p.rs1 == s.p.rs2
      elif s.p.inst == RV64Inst.BNE:
        taken = s.p.rs1 != s.p.rs2
      elif s.p.inst == RV64Inst.BLT:
        taken = s.p.rs1.int() < s.p.rs2.int()
      elif s.p.inst == RV64Inst.BGE:
        taken = s.p.rs1.int() >= s.p.rs2.int()
      elif s.p.inst == RV64Inst.BLTU:
        taken = s.p.rs1.uint() < s.p.rs2.uint()
      elif s.p.inst == RV64Inst.BGEU:
        taken = s.p.rs1.uint() >= s.p.rs2.uint()
      elif s.p.inst == RV64Inst.JAL:
        s.out.next.result = s.p.pc + ILEN_BYTES
        taken = True
      elif s.p.inst == RV64Inst.JALR:
        s.out.next.result = s.p.pc + ILEN_BYTES
        taken = True
        base = s.p.rs1
      else:
        assert False, "invalid branch: {}".format( RV64Inst.name( s.p.inst ) )

      if taken:
        target_pc = base + sext( s.p.imm, XLEN )
      else:
        target_pc = s.p.pc + ILEN_BYTES
      # note that we request a redirect no matter which way the branch went
      # this is because who knows how the branch was predicted
      # the control flow unit maintains information about which way
      # the flow of instructions behind the branch went, and will do nothing
      # if predicted correctly
      creq = RedirectRequest()
      creq.source_tag = s.p.tag
      creq.target_pc = target_pc
      creq.at_commit = 0
      s.controlflow.request_redirect( creq )

    elif s.p.inst == RV64Inst.CSRRW:
      if s.p.rd_valid:
        temp, worked = s.dataflow.read_csr( s.p.csr )
      if not worked:
        s.done.next = 0
        return
      s.out.next.result = temp
      s.dataflow.write_csr( s.p.csr, s.p.rs1 )
    elif s.p.inst == RV64Inst.CSRRS:
      temp, worked = s.dataflow.read_csr( s.p.csr )
      if not worked:
        s.done.next = 0
        return
      s.out.next.result = temp
      # TODO: not quite right because we should attempt to set
      # if the value of rs1 is zero but rs1 is not x0
      if s.p.rs1 != 0:
        s.dataflow.write_csr( s.p.csr, s.out.next.result | s.p.rs1 )
    else:
      raise NotImplementedError( 'Not implemented so sad: ' +
                                 RV64Inst.name( s.p.inst ) )

    s.out.next.pc = s.p.pc
    s.out.next.tag = s.p.tag
    s.done.next = 1
    s.out_valid.next = 1

  def line_trace( s ):
    return LineBlock([
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.out.inst ), s.out.rd_valid, s.out.rd ),
        "res: {}".format( s.out.result )
    ] ).validate( s.out_valid )
