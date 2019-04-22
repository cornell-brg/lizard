from pymtl import *
from lizard.msg.data import *
from lizard.msg.datapath import *
from lizard.msg.control import *
from lizard.util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from lizard.util.line_block import LineBlock
from lizard.util.arch.semantics import sign
from copy import deepcopy


# The integer execute pipe
class ExecuteUnitCL(Model):

  def __init__(s, dataflow, controlflow):
    s.issued_q = InValRdyCLPort(IssuePacket())
    s.result_q = OutValRdyCLPort(ExecutePacket())

    s.dataflow = dataflow
    s.controlflow = controlflow

  def xtick(s):
    if s.reset:
      pass
    if s.result_q.full():
      # Forward
      res = s.result_q.peek()  # Peek at the value in the reg
      if res.rd_valid:
        fwd = PostForwards()
        fwd.tag = res.rd
        fwd.value = res.result
        s.dataflow.forward(fwd)
      return

    if s.issued_q.empty():
      return

    s.current = s.issued_q.deq()

    s.work = ExecutePacket()
    copy_issue_execute(s.current, s.work)

    if s.current.instr_d == RV64Inst.LUI:
      s.work.result = sext(s.current.imm, XLEN)
    elif s.current.instr_d == RV64Inst.AUIPC:
      s.work.result = s.current.pc + sext(s.current.imm, XLEN)
    elif s.current.instr_d == RV64Inst.ADDI:
      s.work.result = s.current.rs1_value + sext(s.current.imm, XLEN)
    elif s.current.instr_d == RV64Inst.SLTI:
      if s.current.rs1_value.int() < s.current.imm.int():
        s.work.result = 1
      else:
        s.work.result = 0
    elif s.current.instr_d == RV64Inst.SLTIU:
      if s.current.rs1_value.uint() < sext(s.current.imm, XLEN).uint():
        s.work.result = 1
      else:
        s.work.result = 0
    elif s.current.instr_d == RV64Inst.XORI:
      s.work.result = s.current.rs1_value ^ sext(s.current.imm, XLEN)
    elif s.current.instr_d == RV64Inst.ORI:
      s.work.result = s.current.rs1_value | sext(s.current.imm, XLEN)
    elif s.current.instr_d == RV64Inst.ANDI:
      s.work.result = s.current.rs1_value & sext(s.current.imm, XLEN)
    elif s.current.instr_d == RV64Inst.SLLI:
      s.work.result = s.current.rs1_value << s.current.imm
    elif s.current.instr_d == RV64Inst.SRLI:
      s.work.result = Bits(
          XLEN, s.current.rs1_value.uint() >> s.current.imm.uint(), trunc=True)
    elif s.current.instr_d == RV64Inst.SRAI:
      s.work.result = Bits(
          XLEN, s.current.rs1_value.int() >> s.current.imm.uint(), trunc=True)
    # Register register insts
    elif s.current.instr_d == RV64Inst.ADD:
      s.work.result = s.current.rs1_value + s.current.rs2_value
    elif s.current.instr_d == RV64Inst.SUB:
      s.work.result = s.current.rs1_value - s.current.rs2_value
    elif s.current.instr_d == RV64Inst.SLL:
      s.work.result = Bits(
          XLEN,
          s.current.rs1_value << s.current.rs2_value[:6].uint(),
          trunc=True)
    elif s.current.instr_d == RV64Inst.SRL:
      s.work.result = Bits(
          XLEN,
          s.current.rs1_value.uint() >> s.current.rs2_value[:6].uint(),
          trunc=True)
    elif s.current.instr_d == RV64Inst.SRA:
      s.work.result = Bits(
          XLEN,
          s.current.rs1_value.int() >> s.current.rs2_value[:6].uint(),
          trunc=True)
    elif s.current.instr_d == RV64Inst.SLT:
      s.work.result = int(s.current.rs1_value.int() < s.current.rs2_value.int())
    elif s.current.instr_d == RV64Inst.SLTU:
      s.work.result = int(
          s.current.rs1_value.uint() < s.current.rs2_value.uint())
    elif s.current.instr_d == RV64Inst.XOR:
      s.work.result = s.current.rs1_value ^ s.current.rs2_value
    elif s.current.instr_d == RV64Inst.OR:
      s.work.result = s.current.rs1_value | s.current.rs2_value
    elif s.current.instr_d == RV64Inst.AND:
      s.work.result = s.current.rs1_value & s.current.rs2_value
    elif s.current.instr_d == RV64Inst.ADDW:
      s.work.result = sext(s.current.rs1_value[:32] + s.current.rs2_value[:32],
                           XLEN)
    elif s.current.instr_d == RV64Inst.SUBW:
      s.work.result = sext(s.current.rs1_value[:32] - s.current.rs2_value[:32],
                           XLEN)
    elif s.current.instr_d == RV64Inst.SLLW:
      s.work.result = sext(
          s.current.rs1_value[:32] << s.current.rs2_value[:5].uint(), XLEN)
    elif s.current.instr_d == RV64Inst.SRLW:
      s.work.result = sext(
          s.current.rs1_value[:32] >> s.current.rs2_value[:5].uint(), XLEN)
    elif s.current.instr_d == RV64Inst.SRAW:
      s.work.result = Bits(
          XLEN,
          s.current.rs1_value[:32].int() >> s.current.rs2_value[:5].uint(),
          trunc=True)
    elif s.current.instr_d == RV64Inst.ADDIW:
      s.work.result = sext(s.current.rs1_value[:32] + s.current.imm[:32], XLEN)
    elif s.current.instr_d == RV64Inst.SLLIW:
      s.work.result = sext(
          Bits(
              32,
              s.current.rs1_value[:32].int() << s.current.imm.uint(),
              trunc=True), XLEN)
    elif s.current.instr_d == RV64Inst.SRLIW:
      s.work.result = sext(s.current.rs1_value[:32] >> s.current.imm.uint(),
                           XLEN)
    elif s.current.instr_d == RV64Inst.SRAIW:
      s.work.result = Bits(
          XLEN,
          s.current.rs1_value[:32].int() >> s.current.imm.uint(),
          trunc=True)
    elif s.current.instr_d in [
        RV64Inst.BEQ, RV64Inst.BNE, RV64Inst.BLT, RV64Inst.BGE, RV64Inst.BLTU,
        RV64Inst.BGEU, RV64Inst.JAL, RV64Inst.JALR
    ]:
      taken = False
      base = s.current.pc
      if s.current.instr_d == RV64Inst.BEQ:
        taken = s.current.rs1_value == s.current.rs2_value
      elif s.current.instr_d == RV64Inst.BNE:
        taken = s.current.rs1_value != s.current.rs2_value
      elif s.current.instr_d == RV64Inst.BLT:
        taken = s.current.rs1_value.int() < s.current.rs2_value.int()
      elif s.current.instr_d == RV64Inst.BGE:
        taken = s.current.rs1_value.int() >= s.current.rs2_value.int()
      elif s.current.instr_d == RV64Inst.BLTU:
        taken = s.current.rs1_value.uint() < s.current.rs2_value.uint()
      elif s.current.instr_d == RV64Inst.BGEU:
        taken = s.current.rs1_value.uint() >= s.current.rs2_value.uint()
      elif s.current.instr_d == RV64Inst.JAL:
        s.work.result = s.current.pc + ILEN_BYTES
        taken = True
      elif s.current.instr_d == RV64Inst.JALR:
        s.work.result = s.current.pc + ILEN_BYTES
        taken = True
        base = s.current.rs1_value
      else:
        assert False, "invalid branch: {}".format(
            RV64Inst.name(s.current.instr_d))

      if taken:
        target_pc = base + sext(s.current.imm, XLEN)

        # if JALR force last bit to 0
        target_pc[0] = 0
      else:
        target_pc = s.current.pc + ILEN_BYTES
      # note that we request a redirect no matter which way the branch went
      # this is because who knows how the branch was predicted
      # the control flow unit maintains information about which way
      # the flow of instructions behind the branch went, and will do nothing
      # if predicted correctly
      creq = RedirectRequest()
      creq.source_tag = s.current.tag
      creq.target_pc = target_pc
      creq.at_commit = 0
      s.controlflow.request_redirect(creq)
    else:
      raise NotImplementedError('Not implemented so sad: %x ' % s.current.opcode
                                + RV64Inst.name(s.current.instr_d))

    # Output the finished instruction
    s.result_q.enq(s.work)
    # Forward
    if s.work.rd_valid:
      fwd = PostForwards()
      fwd.tag = s.work.rd
      fwd.value = s.work.result
      s.dataflow.forward(fwd)

  def line_trace(s):
    return LineBlock([
        "{}".format(s.result_q.msg().tag),
        "{: <8} rd({}): {}".format(
            RV64Inst.name(s.result_q.msg().instr_d),
            s.result_q.msg().rd_valid,
            s.result_q.msg().rd),
        "res: {}".format(s.result_q.msg().result),
    ]).validate(s.result_q.val())
