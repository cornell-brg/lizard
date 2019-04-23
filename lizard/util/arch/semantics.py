from inspect import getargspec
from functools import wraps
from pymtl import Bits, concat
from pymtl.datatypes import helpers
from lizard.config.general import *
from lizard.msg.codes import *
from lizard.util.arch import rv64g


def sign(num):
  return (1, -1)[num < 0]


def sext(bits):
  return helpers.sext(bits, XLEN)


def zext(bits):
  return helpers.zext(bits, XLEN)


def instr(func):

  @wraps(func)
  def exec_instr(self, instr_bits):
    args = [self] + [
        self.isa.fields[x].disassemble(instr_bits)
        for x in getargspec(func).args[1:]
    ]
    return func(*args)

  return exec_instr


class ProcRedirect(object):

  def __init__(self, target):
    self.target = target


class ProcException(object):

  def __init__(self, mcause):
    self.mcause = mcause


class RegisterFile(object):

  def __init__(self):
    self.regs = [Bits(XLEN, 0) for i in xrange(AREG_COUNT)]

  def __getitem__(self, idx):
    if idx == 0:
      return Bits(XLEN, 0)
    else:
      return self.regs[int(idx)]

  def __setitem__(self, idx, value):
    if idx != 0:
      self.regs[idx] = Bits(XLEN, value, trunc=True)


class CsrRegisterFile(object):

  def __init__(self, mngr2proc_queue, proc2mngr_queue):
    self.regs = {}
    self.mngr2proc_queue = mngr2proc_queue
    self.proc2mngr_queue = proc2mngr_queue

  def __getitem__(self, idx):
    if idx == CsrRegisters.mngr2proc:
      return self.mngr2proc_queue.popleft()
    else:
      return self.regs.get(int(idx), Bits(XLEN, 0))

  def __setitem__(self, idx, value):
    trunc = Bits(XLEN, value, trunc=True)
    if idx == CsrRegisters.proc2mngr:
      self.proc2mngr_queue.append(trunc)
    else:
      self.regs[int(idx)] = trunc


class RV64GSemantics(object):

  def __init__(self, memory, mngr2proc_queue, proc2mngr_queue):

    self.PC = Bits(XLEN)
    self.R = RegisterFile()
    self.CSR = CsrRegisterFile(mngr2proc_queue, proc2mngr_queue)
    self.M = memory

    self.isa = rv64g.isa

  def reset(s):
    s.PC = Bits(XLEN, RESET_VECTOR)

  @instr
  def execute_add(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] + s.R[rs2]

  @instr
  def execute_addw(s, rd, rs1, rs2):
    s.R[rd] = sext(s.R[rs1][:32] + s.R[rs2][:32])

  @instr
  def execute_sub(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] - s.R[rs2]

  @instr
  def execute_subw(s, rd, rs1, rs2):
    s.R[rd] = sext(s.R[rs1][:32] - s.R[rs2][:32])

  @instr
  def execute_sll(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] << (s.R[rs2].uint() & 0x3F)

  @instr
  def execute_sllw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.R[rs1][:32] << (s.R[rs2][:32].uint() & 0x1F), trunc=True))

  @instr
  def execute_slt(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1].int() < s.R[rs2].int()

  @instr
  def execute_sltu(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] < s.R[rs2]

  @instr
  def execute_xor(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] ^ s.R[rs2]

  @instr
  def execute_srl(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] >> (s.R[rs2].uint() & 0x3F)

  @instr
  def execute_srlw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.R[rs1][:32] >> (s.R[rs2][:32].uint() & 0x1F), trunc=True))

  @instr
  def execute_sra(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1].int() >> (s.R[rs2].uint() & 0x3F)

  @instr
  def execute_sraw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(
            32,
            s.R[rs1][:32].int() >> (s.R[rs2][:32].uint() & 0x1F),
            trunc=True))

  @instr
  def execute_or(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] | s.R[rs2]

  @instr
  def execute_and(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] & s.R[rs2]

  @instr
  def execute_mul(s, rd, rs1, rs2):
    s.R[rd] = s.R[rs1] * s.R[rs2]

  @instr
  def execute_mulh(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN * 2, s.R[rs1].int() * s.R[rs2].int())[XLEN:2 * XLEN]

  @instr
  def execute_mulhsu(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN * 2, s.R[rs1].int() * s.R[rs2].uint())[XLEN:2 * XLEN]

  @instr
  def execute_mulhu(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN * 2, s.R[rs1].uint() * s.R[rs2].uint())[XLEN:2 * XLEN]

  @instr
  def execute_mulw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.R[rs1][:32].int() * s.R[rs2][:32].int(), trunc=True))

  def sane_divide(s, a, b, bit_len):
    if b == 0:
      return -1
    elif a == -2**(bit_len - 1) and b == -1:
      return a
    else:
      res = abs(a) // abs(b)
      sn = sign(a) * sign(b)
      return res * sn

  @instr
  def execute_div(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN, s.sane_divide(s.R[rs1].int(), s.R[rs2].int(), XLEN))

  @instr
  def execute_divu(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN, s.sane_divide(s.R[rs1].uint(), s.R[rs2].uint(), XLEN))

  @instr
  def execute_divw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.sane_divide(s.R[rs1][:32].int(), s.R[rs2][:32].int(), 32)))

  @instr
  def execute_divuw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.sane_divide(s.R[rs1][:32].uint(), s.R[rs2][:32].uint(), 32)))

  def sane_rem(s, a, b, bit_len):
    if b == 0:
      return a
    elif a == -2**(bit_len - 1) and b == -1:
      return 0
    else:
      res = abs(a) % abs(b)
      sn = sign(a)
      return res * sn

  @instr
  def execute_rem(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN, s.sane_rem(s.R[rs1].int(), s.R[rs2].int(), XLEN))

  @instr
  def execute_remu(s, rd, rs1, rs2):
    s.R[rd] = Bits(XLEN, s.sane_rem(s.R[rs1].uint(), s.R[rs2].uint(), XLEN))

  @instr
  def execute_remw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.sane_rem(s.R[rs1][:32].int(), s.R[rs2][:32].int(), 32)))

  @instr
  def execute_remuw(s, rd, rs1, rs2):
    s.R[rd] = sext(
        Bits(32, s.sane_rem(s.R[rs1][:32].uint(), s.R[rs2][:32].uint(), 32)))

  @instr
  def execute_addi(s, rd, rs1, i_imm):
    s.R[rd] = s.R[rs1] + sext(i_imm)

  @instr
  def execute_addiw(s, rd, rs1, i_imm):
    s.R[rd] = sext(s.R[rs1][:32] + sext(i_imm)[:32])

  @instr
  def execute_slti(s, rd, rs1, i_imm):
    s.R[rd] = s.R[rs1].int() < i_imm.int()

  @instr
  def execute_sltiu(s, rd, rs1, i_imm):
    s.R[rd] = s.R[rs1] < sext(i_imm)

  @instr
  def execute_xori(s, rd, rs1, i_imm):
    s.R[rd] = s.R[rs1] ^ sext(i_imm)

  @instr
  def execute_ori(s, rd, rs1, i_imm):
    s.R[rd] = s.R[rs1] | sext(i_imm)

  @instr
  def execute_andi(s, rd, rs1, i_imm):
    s.R[rd] = s.R[rs1] & sext(i_imm)

  @instr
  def execute_slli(s, rd, rs1, shamt64):
    s.R[rd] = s.R[rs1] << shamt64.uint()

  @instr
  def execute_slliw(s, rd, rs1, shamt32):
    s.R[rd] = sext(Bits(32, s.R[rs1][:32] << shamt32.uint(), trunc=True))

  @instr
  def execute_srli(s, rd, rs1, shamt64):
    s.R[rd] = s.R[rs1] >> shamt64.uint()

  @instr
  def execute_srliw(s, rd, rs1, shamt32):
    s.R[rd] = sext(Bits(32, s.R[rs1][:32] >> shamt32.uint(), trunc=True))

  @instr
  def execute_srai(s, rd, rs1, shamt64):
    s.R[rd] = s.R[rs1].int() >> shamt64.uint()

  @instr
  def execute_sraiw(s, rd, rs1, shamt32):
    s.R[rd] = sext(Bits(32, s.R[rs1][:32].int() >> shamt32.uint(), trunc=True))

  def augment_u_imm(s, u_imm):
    return concat(u_imm, Bits(12, 0))

  @instr
  def execute_lui(s, rd, u_imm):
    s.R[rd] = sext(s.augment_u_imm(u_imm))

  @instr
  def execute_auipc(s, rd, u_imm):
    s.R[rd] = sext(s.augment_u_imm(u_imm)) + s.PC

  @instr
  def execute_lb(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = sext(s.M[addr:addr + 1])

  @instr
  def execute_lh(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = sext(s.M[addr:addr + 2])

  @instr
  def execute_lw(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = sext(s.M[addr:addr + 4])

  @instr
  def execute_ld(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = sext(s.M[addr:addr + 8])

  @instr
  def execute_lbu(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = zext(s.M[addr:addr + 1])

  @instr
  def execute_lhu(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = zext(s.M[addr:addr + 2])

  @instr
  def execute_lwu(s, rd, rs1, i_imm):
    addr = s.R[rs1] + sext(i_imm)
    s.R[rd] = zext(s.M[addr:addr + 4])

  @instr
  def execute_sb(s, rs1, rs2, s_imm):
    addr = s.R[rs1] + sext(s_imm)
    s.M[addr:addr + 1] = s.R[rs2][0:8]

  @instr
  def execute_sh(s, rs1, rs2, s_imm):
    addr = s.R[rs1] + sext(s_imm)
    s.M[addr:addr + 2] = s.R[rs2][0:16]

  @instr
  def execute_sw(s, rs1, rs2, s_imm):
    addr = s.R[rs1] + sext(s_imm)
    s.M[addr:addr + 4] = s.R[rs2][0:32]

  @instr
  def execute_sd(s, rs1, rs2, s_imm):
    addr = s.R[rs1] + sext(s_imm)
    s.M[addr:addr + 8] = s.R[rs2][0:64]

  @instr
  def execute_fence_i(s):
    # fence_i is NOP since we have no pipeline
    pass

  @instr
  def execute_fence(s):
    # fence is NOP since we have no pipeline
    pass

  @instr
  def execute_jal(s, rd, j_imm):
    s.R[rd] = s.PC + 4
    return ProcRedirect(s.PC + sext(j_imm))

  @instr
  def execute_jalr(s, rd, rs1, i_imm):
    temp = s.R[rs1] + sext(i_imm)
    s.R[rd] = s.PC + 4
    return ProcRedirect(temp & 0xFFFFFFFE)

  @instr
  def execute_beq(s, rs1, rs2, b_imm):
    if s.R[rs1] == s.R[rs2]:
      return ProcRedirect(s.PC + sext(b_imm))

  @instr
  def execute_bne(s, rs1, rs2, b_imm):
    if s.R[rs1] != s.R[rs2]:
      return ProcRedirect(s.PC + sext(b_imm))

  @instr
  def execute_blt(s, rs1, rs2, b_imm):
    if s.R[rs1].int() < s.R[rs2].int():
      return ProcRedirect(s.PC + sext(b_imm))

  @instr
  def execute_bge(s, rs1, rs2, b_imm):
    if s.R[rs1].int() >= s.R[rs2].int():
      return ProcRedirect(s.PC + sext(b_imm))

  @instr
  def execute_bltu(s, rs1, rs2, b_imm):
    if s.R[rs1] < s.R[rs2]:
      return ProcRedirect(s.PC + sext(b_imm))

  @instr
  def execute_bgeu(s, rs1, rs2, b_imm):
    if s.R[rs1] >= s.R[rs2]:
      return ProcRedirect(s.PC + sext(b_imm))

  def csr_func(s, rd, csrnum, rs1_is_x0, value, op):
    csr = int(csrnum)
    if not CsrRegisters.contains(csr):
      return ProcException(ExceptionCode.ILLEGAL_INSTRUCTION)
    else:
      s.R[rd] = s.CSR[csr]
      return op(csr, rs1_is_x0, value)

  def csr_reg_func(s, rd, csrnum, rs1, op):
    return s.csr_func(rd, csrnum, rs1 == 0, s.R[rs1], op)

  def csr_imm_func(s, rd, csrnum, rs1, op):
    return s.csr_func(rd, csrnum, False, zext(rs1), op)

  def csrrw_op(s, csr, rs1_is_x0, value):
    s.CSR[csr] = value

  def csrrs_op(s, csr, rs1_is_x0, value):
    if not rs1_is_x0:
      s.CSR[csr] = s.CSR[csr] | value

  def csrrc_op(s, csr, rs1_is_x0, value):
    if not rs1_is_x0:
      s.CSR[csr] = s.CSR[csr] & (not value)

  @instr
  def execute_csrrw(s, rd, csrnum, rs1):
    return s.csr_reg_func(rd, csrnum, rs1, s.csrrw_op)

  @instr
  def execute_csrrs(s, rd, csrnum, rs1):
    return s.csr_reg_func(rd, csrnum, rs1, s.csrrs_op)

  @instr
  def execute_csrrc(s, rd, csrnum, rs1):
    return s.csr_reg_func(rd, csrnum, rs1, s.csrrc_op)

  @instr
  def execute_csrrwi(s, rd, csrnum, rs1):
    return s.csr_imm_func(rd, csrnum, rs1, s.csrrw_op)

  @instr
  def execute_csrrsi(s, rd, csrnum, rs1):
    return s.csr_imm_func(rd, csrnum, rs1, s.csrrw_op)

  @instr
  def execute_csrrci(s, rd, csrnum, rs1):
    return s.csr_imm_func(rd, csrnum, rs1, s.csrrc_op)

  @instr
  def execute_invld(s):
    return ProcException(ExceptionCode.ILLEGAL_INSTRUCTION)

  @instr
  def execute_ecall(s):
    return ProcException(ExceptionCode.ENVIRONMENT_CALL_FROM_U)

  @instr
  def execute_ebreak(s):
    return ProcException(ExceptionCode.BREAKPOINT)

  def handle_exception(s, instr, packet):
    s.CSR[CsrRegisters.mtval] = instr
    s.CSR[CsrRegisters.mcause] = packet.mcause
    s.CSR[CsrRegisters.mepc] = s.PC

    mtvec = s.CSR[CsrRegisters.mtvec]
    mode = mtvec[0:2]
    base = concat(mtvec[2:XLEN], Bits(2, 0))
    if mode == MtvecMode.direct:
      target = base
    elif mode == MtvecMode.vectored:
      target = base + (packet.mcause << 2)
    else:
      # this is a bad state. mtvec is curcial to handling
      # exceptions, and there is no way to handle and exception
      # related to mtvec.
      # In a real processor, this would probably just halt or reset
      # the entire processor
      assert False
    s.PC = target

  def execute(self, inst):
    foo = getattr(
        self, 'execute_{}'.format(
            self.isa.decode_inst_name(inst).replace('.', '_')))
    result = foo(inst)
    if isinstance(result, ProcException):
      self.handle_exception(inst, result)
    elif isinstance(result, ProcRedirect):
      self.PC = result.target
    else:
      self.PC += ILEN_BYTES
