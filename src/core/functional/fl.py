from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.functional import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from util.line_block import LineBlock


class FunctionalFL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.issued = InValRdyBundle( IssuePacket() )
    s.result = OutValRdyBundle( FunctionalPacket() )

    s.issued_q = InValRdyQueueAdapterFL( s.issued )
    s.result_q = OutValRdyQueueAdapterFL( s.result )

    s.dataflow = dataflow
    s.controlflow = controlflow

    s.out = FunctionalPacket()

    @s.tick_fl
    def tick():
      p = s.issued_q.popleft()

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

      s.out = FunctionalPacket()
      s.out.inst = p.inst
      s.out.rd_valid = p.rd_valid
      s.out.rd = p.rd
      # IMMs
      if p.inst == RV64Inst.ADDI:
        s.out.result = p.rs1 + sext( p.imm, XLEN )
      elif p.inst == RV64Inst.SLTI:
        if p.rs1.int() < p.imm.int():
          s.out.result = 1
        else:
          s.out.result = 0
      elif p.inst == RV64Inst.SLTIU:
        if p.rs1.uint() < p.imm.uint():
          s.out.result = 1
        else:
          s.out.result = 0
      elif p.inst == RV64Inst.XORI:
        s.out.result = p.rs1 ^ sext( p.imm, XLEN )
      elif p.inst == RV64Inst.ORI:
        s.out.result = p.rs1 | sext( p.imm, XLEN )
      elif p.inst == RV64Inst.ANDI:
        s.out.result = p.rs1 & sext( p.imm, XLEN )
      elif p.inst == RV64Inst.SLLI:
        s.out.result = p.rs1 << p.imm
      elif p.inst == RV64Inst.SRLI:
        s.out.result = Bits( XLEN, p.rs1.uint() >> p.imm.uint(), trunc=True )
      elif p.inst == RV64Inst.SRAI:
        s.out.result = Bits( XLEN, p.rs1.int() >> p.imm.uint(), trunc=True )
      # Register register insts
      elif p.inst == RV64Inst.ADD:
        s.out.result = p.rs1 + p.rs2
      elif p.inst == RV64Inst.SUB:
        s.out.result = p.rs1 - p.rs2
      elif p.inst == RV64Inst.SLL:
        s.out.result = p.rs1 << p.rs2
      elif p.inst == RV64Inst.SRL:
        s.out.result = p.rs1 >> p.rs2
      elif p.inst == RV64Inst.SLT:
        s.out.result = int(p.rs1.int() < p.rs2.int())
      elif p.inst == RV64Inst.SLTU:
        s.out.result = int(p.rs1.uint() < p.rs2.uint())
      elif p.inst == RV64Inst.XOR:
        s.out.result = p.rs1 ^ p.rs2
      elif p.inst == RV64Inst.OR:
        s.out.result = p.rs1 | p.rs2
      elif p.inst == RV64Inst.AND:
        s.out.result = p.rs1 & p.rs2
      elif p.inst == RV64Inst.SRA:
        s.out.result = Bits( XLEN, p.rs1.int() >> p.rs2.uint(), trunc=True )
      # Branches
      elif p.is_branch:
        taken = False
        base = p.pc
        if p.inst == RV64Inst.BEQ:
          taken = p.rs1 == p.rs2
        elif p.inst == RV64Inst.BNE:
          taken = p.rs1 != p.rs2
        elif p.inst == RV64Inst.BLT:
          taken = p.rs1.int() < p.rs2.int()
        elif p.inst == RV64Inst.BGE:
          taken = p.rs1.int() >= p.rs2.int()
        elif p.inst == RV64Inst.BLTU:
          taken = p.rs1.uint() < p.rs2.uint()
        elif p.inst == RV64Inst.BGEU:
          taken = p.rs1.uint() >= p.rs2.uint()
        elif p.inst == RV64Inst.JAL:
          print( 'hi: {}'.format( p.pc + ILEN_BYTES ) )
          s.out.result = p.pc + ILEN_BYTES
          taken = True
        elif p.inst == RV64Inst.JALR:
          s.out.result = p.pc + ILEN_BYTES
          taken = True
          base = p.rs1
        else:
          assert False, "invalid branch: {}".format( RV64Inst.name( p.inst ) )

        if taken:
          target_pc = base + sext( p.imm, XLEN )
        else:
          target_pc = p.pc + ILEN_BYTES
        # note that we request a redirect no matter which way the branch went
        # this is because who knows how the branch was predicted
        # the control flow unit maintains information about which way
        # the flow of instructions behind the branch went, and will do nothing
        # if predicted correctly
        creq = RedirectRequest()
        creq.source_tag = p.tag
        creq.target_pc = target_pc
        creq.at_commit = 0
        s.controlflow.request_redirect( creq )

      elif p.inst == RV64Inst.CSRRW:
        if p.rd_valid:
          s.out.result = s.dataflow.read_csr( p.csr )
        s.dataflow.write_csr( p.csr, p.rs1 )
      elif p.inst == RV64Inst.CSRRS:
        s.out.result = s.dataflow.read_csr( p.csr )
        # TODO: not quite right because we should attempt to set
        # if the value of rs1 is zero but rs1 is not x0
        if p.rs1 != 0:
          s.dataflow.write_csr( p.csr, s.out.result | p.rs1 )
      else:
        raise NotImplementedError( 'Not implemented so sad: ' +
                                   RV64Inst.name( p.inst ) )

      s.out.pc = p.pc
      s.out.tag = p.tag
      s.result_q.append( s.out )

  def line_trace( s ):
    return LineBlock([
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.out.inst ), s.out.rd_valid, s.out.rd ),
        "res: {}".format( s.out.result )
    ] )
