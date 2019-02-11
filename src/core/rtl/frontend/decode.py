from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from msg.codes import RVInstMask, Opcode, ExceptionCode

from core.rtl.frontend.fetch import FetchInterface
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.messages import FetchMsg, DecodeMsg, PipelineMsg
from core.rtl.micro_op import MicroOp


class DecodeInterface(Interface):

  def __init__(s):
    super(DecodeInterface, s).__init__(
        [
            MethodSpec(
                'get',
                args={},
                rets={
                    'msg': DecodeMsg(),
                },
                call=True,
                rdy=True,
            ),
        ],
        ordering_chains=[
            [],
        ],
    )


class Decode(Model):

  def __init__(s, xlen, ilen, areg_tag_nbits, imm_len, seq_nbits):
    UseInterface(s, DecodeInterface())

    s.fetch = FetchInterface(ilen)
    s.fetch.require(s, 'fetch', 'get')

    s.cflow = ControlFlowManagerInterface(xlen, seq_nbits)
    s.cflow.require(s, 'cflow', 'check_redirect')

    # Outgoing pipeline register
    s.decmsg_val_ = RegRst(Bits(1), reset_value=0)
    s.decmsg_ = Wire(DecodeMsg())

    s.dec_ = Wire(DecodeMsg())
    s.rdy_ = Wire(1)
    s.accepted_ = Wire(1)
    s.msg_ = Wire(FetchMsg())
    s.inst_ = Wire(Bits(ilen))

    s.dec_fail_ = Wire(1)

    # TODO: remove this once this connects to the next stage
    s.connect(s.get_call, s.get_rdy)
    s.connect_wire(s.inst_, s.msg_.inst)

    s.opcode_ = Wire(s.inst_[RVInstMask.OPCODE].nbits)
    s.connect_wire(s.opcode_, s.inst_[RVInstMask.OPCODE])
    s.func3_ = Wire(s.inst_[RVInstMask.FUNCT3].nbits)
    s.connect_wire(s.func3_, s.inst_[RVInstMask.FUNCT3])
    s.func7_ = Wire(s.inst_[RVInstMask.FUNCT7].nbits)
    s.connect_wire(s.func7_, s.inst_[RVInstMask.FUNCT7])
    s.rs1_ = Wire(s.inst_[RVInstMask.RS1].nbits)
    s.connect_wire(s.rs1_, s.inst_[RVInstMask.RS1])
    s.rs2_ = Wire(s.inst_[RVInstMask.RS2].nbits)
    s.connect_wire(s.rs2_, s.inst_[RVInstMask.RS2])
    s.rd_ = Wire(s.inst_[RVInstMask.RD].nbits)
    s.connect_wire(s.rd_, s.inst_[RVInstMask.RD])
    s.fence_upper_ = Wire(s.inst_[RVInstMask.FENCE_UPPER].nbits)
    s.connect_wire(s.fence_upper_, s.inst_[RVInstMask.FENCE_UPPER])

    s.connect(s.msg_, s.fetch_get_msg)
    s.connect(s.fetch_get_call, s.accepted_)

    # All the MicroOps
    # OP-IMM
    s.dec_opimm_fail_ = Wire(1)
    s.uop_opimm_ = Wire(MicroOp.bits)
    # OP
    s.dec_op_fail_ = Wire(1)
    s.uop_op_ = Wire(MicroOp.bits)
    # OP-IMM-32
    s.dec_opimm32_fail_ = Wire(1)
    s.uop_opimm32_ = Wire(MicroOp.bits)
    # OP-32
    s.dec_op_32_fail_ = Wire(1)
    s.uop_op_32_ = Wire(MicroOp.bits)
    # LOAD
    s.dec_load_fail_ = Wire(1)
    s.uop_load_ = Wire(MicroOp.bits)
    # STORE
    s.dec_store_fail_ = Wire(1)
    s.uop_store_ = Wire(MicroOp.bits)
    # BRANCH
    s.dec_branch_fail_ = Wire(1)
    s.uop_branch_ = Wire(MicroOp.bits)
    # SYSTEM
    s.dec_system_fail_ = Wire(1)
    s.uop_system_ = Wire(MicroOp.bits)
    # MISC_MEM
    s.dec_misc_mem_fail_ = Wire(1)
    s.uop_misc_mem_ = Wire(MicroOp.bits)


    # All the IMMs
    s.imm_i_ = Wire(imm_len)
    s.imm_s_ = Wire(imm_len)
    s.imm_b_ = Wire(imm_len)
    s.imm_u_ = Wire(imm_len)
    s.imm_j_ = Wire(imm_len)

    @s.combinational
    def handle_imm():
      s.imm_i_.v = sext(s.inst_[RVInstMask.I_IMM], imm_len)
      s.imm_s_.v = sext(
          concat(s.inst_[RVInstMask.S_IMM1], s.inst_[RVInstMask.S_IMM0]),
          imm_len)
      s.imm_b_.v = sext(
          concat(s.inst_[RVInstMask.B_IMM3], s.inst_[RVInstMask.B_IMM2],
                 s.inst_[RVInstMask.B_IMM1], s.inst_[RVInstMask.B_IMM0]) << 1,
          imm_len)
      s.imm_u_.v = sext(s.inst_[RVInstMask.U_IMM], imm_len)
      s.imm_j_.v = sext(
          concat(s.inst_[RVInstMask.J_IMM3], s.inst_[RVInstMask.J_IMM2],
                 s.inst_[RVInstMask.J_IMM1], s.inst_[RVInstMask.J_IMM0]) << 1,
          imm_len)

    @s.combinational
    def handle_flags():
      # Ready when pipeline register is invalid or being read from this cycle
      s.rdy_.v = not s.decmsg_val_.out or s.get_call
      s.accepted_.v = s.rdy_ and s.fetch_get_rdy

    @s.combinational
    def set_valreg():
      s.decmsg_val_.in_.v = s.accepted_ or (s.decmsg_val_.out and
                                            not s.get_call)
      s.get_rdy.v = s.decmsg_val_.out if not s.cflow_check_redirect_redirect else 0

    @s.combinational
    def decode():
      s.dec_fail_.v = 1
      s.dec_.rs1.v = s.rs1_
      s.dec_.rs2.v = s.rs2_
      s.dec_.rd.v = s.rd_
      s.dec_.rs1_val.v = 0
      s.dec_.rs2_val.v = 0
      s.dec_.rd_val.v = 0
      s.dec_.imm_val.v = 0
      s.dec_.trap.v = 0
      s.dec_.mcause.v = 0
      s.dec_.mtval.v = 0
      # If there is already an exception, propogate it
      if s.msg_.trap != 0:
        s.dec_.trap.v = s.msg_.trap
        s.dec_.mcause.v = s.msg_.mcause
        s.dec_.mtval.v = s.msg_.mtval
      if s.opcode_ == Opcode.LOAD:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_load_
        s.dec_fail_.v = s.dec_load_fail_
#     elif s.opcode_ == Opcode.LOAD_FP:
      elif s.opcode_ == Opcode.MISC_MEM:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_misc_mem_
        s.dec_fail_.v = s.dec_misc_mem_fail_
      elif s.opcode_ == Opcode.OP_IMM:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_opimm_
        s.dec_fail_.v = s.dec_opimm_fail_
      elif s.opcode_ == Opcode.AUIPC:
        s.dec_.rd_val.v = 1
        # U-type imm
        s.dec_.imm.v = s.imm_u_
        s.dec_.uop.v = MicroOp.AUPIC
        s.dec_fail_.v = 0
      elif s.opcode_ == Opcode.OP_IMM_32:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_opimm32_
        s.dec_fail_.v = s.dec_opimm32_fail_
      elif s.opcode_ == Opcode.STORE:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.imm_val.v = 1
        # S-type imm
        s.dec_.imm.v = s.imm_s_
        s.dec_.uop.v = s.uop_store_
        s.dec_fail_.v = s.dec_store_fail_
#     elif s.opcode_ == Opcode.STORE_FP:
      elif s.opcode_ == Opcode.AMO:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.rd_val.v = 1
      elif s.opcode_ == Opcode.OP:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.uop.v = s.uop_op_
        s.dec_fail_.v = s.dec_op_fail_
      elif s.opcode_ == Opcode.LUI:
        s.dec_.rd_val.v = 1
        # U-type imm
        s.dec_.imm.v = s.imm_u_
        s.dec_.uop.v = MicroOp.LUI
        s.dec_fail_.v = 0
      elif s.opcode_ == Opcode.OP_32:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.uop.v = s.uop_op_32_
        s.dec_fail_.v = s.dec_op_32_fail_


#     elif s.opcode_ == Opcode.MADD:
#     elif s.opcode_ == Opcode.MSUB:
#     elif s.opcode_ == Opcode.NMSUB:
#     elif s.opcode_ == Opcode.NMADD:
#     elif s.opcode_ == Opcode.OP_FP:
      elif s.opcode_ == Opcode.BRANCH:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.imm_val.v = 1
        # B-type imm
        s.dec_.imm.v = s.imm_b_
        s.dec_.uop.v = s.uop_branch_
        s.dec_fail_.v = s.dec_branch_fail_
      elif s.opcode_ == Opcode.JALR:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # J-type imm
        s.dec_.imm.v = s.imm_j_
        s.dec_.uop.v = MicroOp.JALR
        s.dec_fail_.v = 0
      elif s.opcode_ == Opcode.JAL:
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # J-type imm
        s.dec_.imm.v = s.imm_j_
        s.dec_.uop.v = MicroOp.JAL
        s.dec_fail_.v = 0
      elif s.opcode_ == Opcode.SYSTEM:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_system_
        s.dec_fail_.v = s.dec_system_fail_

      # Handle illegal instruction exception
      if s.dec_fail_:
        s.dec_.trap.v = 1
        s.dec_.mcause.v = ExceptionCode.ILLEGAL_INSTRUCTION
        s.dec_.mtval.v = zext(s.inst_, xlen)

    # Handle the annoying funct7_shift case
    s.func7_shft_ = Wire(s.inst_[RVInstMask.FUNCT7_SHFT64].nbits)
    s.connect(s.func7_shft_, s.inst_[RVInstMask.FUNCT7_SHFT64])

    @s.combinational
    def decode_op_imm():
      s.dec_opimm_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_opimm_.v = MicroOp.ADDI
      elif s.func3_ == 0b010:
        s.uop_opimm_.v = MicroOp.SLTI
      elif s.func3_ == 0b011:
        s.uop_opimm_.v = MicroOp.SLTIU
      elif s.func3_ == 0b100:
        s.uop_opimm_.v = MicroOp.XORI
      elif s.func3_ == 0b110:
        s.uop_opimm_.v = MicroOp.ORI
      elif s.func3_ == 0b111:
        s.uop_opimm_.v = MicroOp.ANDI
      elif s.func3_ == 0b001 and s.func7_shft_ == 0:
        s.uop_opimm_.v = MicroOp.SLLI
      elif s.func3_ == 0b101 and s.func7_shft_ == 0:
        s.uop_opimm_.v = MicroOp.SRLI
      elif s.func3_ == 0b101 and s.func7_shft_ == 0b010000:
        s.uop_opimm_.v = MicroOp.SRAI
      else:  # Illegal
        s.uop_opimm_.v = 0
        s.dec_opimm_fail_.v = 1

    @s.combinational
    def decode_op_imm32():
      s.dec_opimm32_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_opimm32_.v = MicroOp.ADDIW
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_opimm32_.v = MicroOp.SLLIW
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_opimm32_.v = MicroOp.SRLIW
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_opimm32_.v = MicroOp.SRAIW
      else:  # Illegal
        s.uop_opimm32_.v = 0
        s.dec_opimm32_fail_.v = 1

    @s.combinational
    def decode_op_32():
      s.dec_op_32_fail_.v = 0
      if s.func3_ == 0b000 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.ADDW
      elif s.func3_ == 0b000 and s.func7_ == 0b0100000:
        s.uop_op_32_.v = MicroOp.SUBW
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.SLLW
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.SRLW
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_op_32_.v = MicroOp.SRAW
      else:  # Illegal
        s.uop_op_32_.v = 0
        s.dec_op_32_fail_.v = 1

    @s.combinational
    def decode_op():
      s.dec_op_fail_.v = 0
      if s.func3_ == 0b000 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.ADD
      elif s.func3_ == 0b000 and s.func7_ == 0b0100000:
        s.uop_op_.v = MicroOp.SUB
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.SLL
      elif s.func3_ == 0b010 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.SLT
      elif s.func3_ == 0b011 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.SLTU
      elif s.func3_ == 0b100 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.XOR
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.SRL
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_op_.v = MicroOp.SRA
      elif s.func3_ == 0b110 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.OR
      elif s.func3_ == 0b111 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.AND
      else:  # Illegal
        s.uop_op_.v = 0
        s.dec_op_fail_.v = 1

    @s.combinational
    def decode_load():
      s.dec_load_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_load_.v = MicroOp.LB
      elif s.func3_ == 0b001:
        s.uop_load_.v = MicroOp.LH
      elif s.func3_ == 0b010:
        s.uop_load_.v = MicroOp.LW
      elif s.func3_ == 0b011:
        s.uop_load_.v = MicroOp.LD
      elif s.func3_ == 0b100:
        s.uop_load_.v = MicroOp.LBU
      elif s.func3_ == 0b101:
        s.uop_load_.v = MicroOp.LHU
      elif s.func3_ == 0b110:
        s.uop_load_.v = MicroOp.LWU
      else:  # Illegal
        s.uop_load_.v = 0
        s.dec_load_fail_.v = 1

    @s.combinational
    def decode_store():
      s.dec_store_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_store_.v = MicroOp.SB
      elif s.func3_ == 0b001:
        s.uop_store_.v = MicroOp.SH
      elif s.func3_ == 0b010:
        s.uop_store_.v = MicroOp.SW
      elif s.func3_ == 0b011:
        s.uop_store_.v = MicroOp.SD
      else:  # Illegal
        s.uop_store_.v = 0
        s.dec_store_fail_.v = 1


    @s.combinational
    def decode_branch():
      s.dec_branch_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_branch_.v = MicroOp.BEQ
      elif s.func3_ == 0b001:
        s.uop_branch_.v = MicroOp.BNE
      if s.func3_ == 0b100:
        s.uop_branch_.v = MicroOp.BLT
      if s.func3_ == 0b101:
        s.uop_branch_.v = MicroOp.BGE
      if s.func3_ == 0b110:
        s.uop_branch_.v = MicroOp.BLTU
      if s.func3_ == 0b111:
        s.uop_branch_.v = MicroOp.BGEU
      else: # Illegal
        s.uop_branch_.v = 0
        s.dec_branch_fail_.v = 1


    @s.combinational
    def decode_system():
      s.dec_system_fail_.v = 0
      if s.imm_i_ == 0 and s.rs1_ == 0 and s.func3_ == 0 and s.rd_ == 0:
        s.uop_system_.v = MicroOp.ECALL
      elif s.imm_i_ == 0b1 and s.rs1_ == 0 and s.func3_ == 0 and s.rs2_ == 0:
        s.uop_system_.v = MicroOp.EBREAK
      elif s.func3_ == 0b001:
        s.uop_system_.v = MicroOp.CSRRW
      elif s.func3_ == 0b010:
        s.uop_system_.v = MicroOp.CSRRS
      elif s.func3_ == 0b011:
        s.uop_system_.v = MicroOp.CSRRC
      elif s.func3_ == 0b101:
        s.uop_system_.v = MicroOp.CSRRWI
      elif s.func3_ == 0b110:
        s.uop_system_.v = MicroOp.CSRRSI
      elif s.func3_ == 0b111:
        s.uop_system_.v = MicroOp.CSRRCI
      else: # Illegal
        s.uop_system_.v = 0
        s.dec_system_fail_.v = 1

    @s.combinational
    def decode_misc_mem():
      s.dec_misc_mem_fail_.v = 0
      if s.fence_upper_ == 0 and s.rs1_ == 0 and s.func3_ == 0 and s.rd_ == 0:
        s.uop_misc_mem_.v = MicroOp.FENCE
      elif s.imm_i_ == 0 and s.rs1_ == 0 and s.func3_ == 0b001 and s.rd_ == 0:
        s.uop_misc_mem_.v = MicroOp.FENCE_I
      else: # Illegal
        s.uop_misc_mem_.v = 0
        s.dec_misc_mem_fail_.v = 1

    @s.tick_rtl
    def update_out():
      if s.accepted_:
        s.decmsg_.n = s.dec_

  def line_trace(s):
    return str(s.decmsg_)
