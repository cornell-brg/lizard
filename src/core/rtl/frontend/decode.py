from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from msg.codes import RVInstMask, Opcode, ExceptionCode

from core.rtl.frontend.fetch import FetchInterface
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.messages import FetchMsg, DecodeMsg, PipelineMsg, ExecPipe
from core.rtl.micro_op import MicroOp


class DecodeInterface(Interface):

  def __init__(s, dlen, ilen, imm_len):
    s.DataLen = dlen
    s.InstLen = ilen
    s.ImmLen = imm_len
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

  def __init__(s, decode_interface, fetch_interface, cflow_interface):
    UseInterface(s, decode_interface)
    xlen = s.interface.DataLen
    ilen = s.interface.InstLen
    imm_len = s.interface.ImmLen

    s.fetch = fetch_interface
    s.fetch.require(s, 'fetch', 'get')

    s.cflow = cflow_interface
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
    s.pipe_op_ = Wire(ExecPipe.bits)
    # OP-IMM-32
    s.dec_opimm32_fail_ = Wire(1)
    s.uop_opimm32_ = Wire(MicroOp.bits)
    # OP-32
    s.dec_op_32_fail_ = Wire(1)
    s.uop_op_32_ = Wire(MicroOp.bits)
    s.pipe_op_32_ = Wire(ExecPipe.bits)
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
    # PYMTL_BROKEN: sext(concat()) does not work!
    s.imm_i_ = Wire(imm_len)
    s.imm_concat_i_ = Wire(s.inst_[RVInstMask.I_IMM].nbits)

    s.imm_concat_s_ = Wire(s.inst_[RVInstMask.S_IMM1].nbits +
                           s.inst_[RVInstMask.S_IMM0].nbits)
    s.imm_s_ = Wire(imm_len)

    s.imm_concat_b_ = Wire(
        s.inst_[RVInstMask.B_IMM3].nbits + s.inst_[RVInstMask.B_IMM2].nbits +
        s.inst_[RVInstMask.B_IMM1].nbits + s.inst_[RVInstMask.B_IMM0].nbits + 1)
    s.imm_b_ = Wire(imm_len)

    s.imm_concat_u_ = Wire(s.inst_[RVInstMask.U_IMM].nbits)
    s.imm_u_ = Wire(imm_len)

    s.imm_concat_j_ = Wire(
        s.inst_[RVInstMask.J_IMM3].nbits + s.inst_[RVInstMask.J_IMM2].nbits +
        s.inst_[RVInstMask.J_IMM1].nbits + s.inst_[RVInstMask.J_IMM0].nbits + 1)
    s.imm_j_ = Wire(imm_len)

    @s.combinational
    def handle_imm():
      # I-type
      s.imm_concat_i_.v = s.inst_[RVInstMask.I_IMM]
      s.imm_i_.v = sext(s.imm_concat_i_, imm_len)
      # S-Type
      s.imm_concat_s_.v = concat(s.inst_[RVInstMask.S_IMM1],
                                 s.inst_[RVInstMask.S_IMM0])
      s.imm_s_.v = sext(s.imm_concat_s_, imm_len)
      # # B-type
      s.imm_concat_b_.v = (
          concat(s.inst_[RVInstMask.B_IMM3], s.inst_[RVInstMask.B_IMM2],
                 s.inst_[RVInstMask.B_IMM1], s.inst_[RVInstMask.B_IMM0],
                 Bits(1, 0)))
      s.imm_b_.v = sext(s.imm_concat_b_, imm_len)
      # # U type
      s.imm_concat_u_.v = s.inst_[RVInstMask.U_IMM]
      s.imm_u_.v = sext(s.imm_concat_u_, imm_len)
      # # J-type
      s.imm_concat_j_.v = concat(
          s.inst_[RVInstMask.J_IMM3], s.inst_[RVInstMask.J_IMM2],
          s.inst_[RVInstMask.J_IMM1], s.inst_[RVInstMask.J_IMM0], Bits(1, 0))
      s.imm_j_.v = sext(s.imm_concat_j_, imm_len)

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
      s.dec_.exec_pipe.v = 0
      s.dec_.pc_succ.v = s.msg_.pc_succ # Propogate successor info
      s.dec_.speculative.v = 0
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
        s.dec_.exec_pipe.v = ExecPipe.AGU_PIPE
#     elif s.opcode_ == Opcode.LOAD_FP:
      elif s.opcode_ == Opcode.MISC_MEM:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_misc_mem_
        s.dec_fail_.v = s.dec_misc_mem_fail_
        s.dec_.exec_pipe.v = ExecPipe.AGU_PIPE
      elif s.opcode_ == Opcode.OP_IMM:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_opimm_
        s.dec_fail_.v = s.dec_opimm_fail_
        s.dec_.exec_pipe.v = ExecPipe.ALU_PIPE
      elif s.opcode_ == Opcode.AUIPC:
        s.dec_.rd_val.v = 1
        # U-type imm
        s.dec_.imm.v = s.imm_u_
        s.dec_.uop.v = MicroOp.UOP_AUIPC
        s.dec_fail_.v = 0
        s.dec_.exec_pipe.v = ExecPipe.ALU_PIPE
      elif s.opcode_ == Opcode.OP_IMM_32:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_opimm32_
        s.dec_fail_.v = s.dec_opimm32_fail_
        s.dec_.exec_pipe.v = ExecPipe.ALU_PIPE
      elif s.opcode_ == Opcode.STORE:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.imm_val.v = 1
        # S-type imm
        s.dec_.imm.v = s.imm_s_
        s.dec_.uop.v = s.uop_store_
        s.dec_fail_.v = s.dec_store_fail_
        s.dec_.exec_pipe.v = ExecPipe.AGU_PIPE
#     elif s.opcode_ == Opcode.STORE_FP:
#     elif s.opcode_ == Opcode.AMO:
      elif s.opcode_ == Opcode.OP:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.uop.v = s.uop_op_
        s.dec_fail_.v = s.dec_op_fail_
        s.dec_.exec_pipe.v = s.pipe_op_
      elif s.opcode_ == Opcode.LUI:
        s.dec_.rd_val.v = 1
        # U-type imm
        s.dec_.imm.v = s.imm_u_
        s.dec_.uop.v = MicroOp.UOP_LUI
        s.dec_fail_.v = 0
        s.dec_.exec_pipe.v = ExecPipe.ALU_PIPE
      elif s.opcode_ == Opcode.OP_32:
        s.dec_.rs1_val.v = 1
        s.dec_.rs2_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.uop.v = s.uop_op_32_
        s.dec_fail_.v = s.dec_op_32_fail_
        s.dec_.exec_pipe.v = s.pipe_op_32_


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
        s.dec_.exec_pipe.v = ExecPipe.BRANCH_PIPE
        s.dec_.speculative.v = 1  # Mark as speculative!
      elif s.opcode_ == Opcode.JALR:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # J-type imm
        s.dec_.imm.v = s.imm_j_
        s.dec_.uop.v = MicroOp.UOP_JALR
        s.dec_fail_.v = 0
        s.dec_.exec_pipe.v = ExecPipe.BRANCH_PIPE
        s.dec_.speculative.v = 1  # Mark as speculative!
      elif s.opcode_ == Opcode.JAL:
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # J-type imm
        s.dec_.imm.v = s.imm_j_
        s.dec_.uop.v = MicroOp.UOP_JAL
        s.dec_fail_.v = 0
        s.dec_.exec_pipe.v = ExecPipe.BRANCH_PIPE
        s.dec_.speculative.v = 1  # Mark as speculative!
      elif s.opcode_ == Opcode.SYSTEM:
        s.dec_.rs1_val.v = 1
        s.dec_.rd_val.v = 1
        s.dec_.imm_val.v = 1
        # I-type imm
        s.dec_.imm.v = s.imm_i_
        s.dec_.uop.v = s.uop_system_
        s.dec_fail_.v = s.dec_system_fail_
        s.dec_.exec_pipe.v = ExecPipe.CSR_PIPE

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
        s.uop_opimm_.v = MicroOp.UOP_ADDI
      elif s.func3_ == 0b010:
        s.uop_opimm_.v = MicroOp.UOP_SLTI
      elif s.func3_ == 0b011:
        s.uop_opimm_.v = MicroOp.UOP_SLTIU
      elif s.func3_ == 0b100:
        s.uop_opimm_.v = MicroOp.UOP_XORI
      elif s.func3_ == 0b110:
        s.uop_opimm_.v = MicroOp.UOP_ORI
      elif s.func3_ == 0b111:
        s.uop_opimm_.v = MicroOp.UOP_ANDI
      elif s.func3_ == 0b001 and s.func7_shft_ == 0:
        s.uop_opimm_.v = MicroOp.UOP_SLLI
      elif s.func3_ == 0b101 and s.func7_shft_ == 0:
        s.uop_opimm_.v = MicroOp.UOP_SRLI
      elif s.func3_ == 0b101 and s.func7_shft_ == 0b010000:
        s.uop_opimm_.v = MicroOp.UOP_SRAI
      else:  # Illegal
        s.uop_opimm_.v = 0
        s.dec_opimm_fail_.v = 1

    @s.combinational
    def decode_op_imm32():
      s.dec_opimm32_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_opimm32_.v = MicroOp.UOP_ADDIW
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_opimm32_.v = MicroOp.UOP_SLLIW
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_opimm32_.v = MicroOp.UOP_SRLIW
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_opimm32_.v = MicroOp.UOP_SRAIW
      else:  # Illegal
        s.uop_opimm32_.v = 0
        s.dec_opimm32_fail_.v = 1

    @s.combinational
    def decode_op_32():
      s.dec_op_32_fail_.v = 0
      # Pick the correct execution pipe:
      s.pipe_op_.v = ExecPipe.MULDIV_PIPE if s.func7_ == 0b1 else ExecPipe.ALU_PIPE
      if s.func3_ == 0b000 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.UOP_ADDW
      elif s.func3_ == 0b000 and s.func7_ == 0b0100000:
        s.uop_op_32_.v = MicroOp.UOP_SUBW
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.UOP_SLLW
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_op_32_.v = MicroOp.UOP_SRLW
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_op_32_.v = MicroOp.UOP_SRAW
      elif s.func3_ == 0b000 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_MULW
      elif s.func3_ == 0b100 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_DIVW
      elif s.func3_ == 0b101 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_DIVUW
      elif s.func3_ == 0b110 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_REMW
      elif s.func3_ == 0b111 and s.func7_ == 0b1:
        s.uop_op_32_.v = MicroOp.UOP_REMUW
      else:  # Illegal
        s.uop_op_32_.v = 0
        s.dec_op_32_fail_.v = 1

    @s.combinational
    def decode_op():
      s.dec_op_fail_.v = 0
      # Pick the correct execution pipe:
      s.pipe_op_.v = ExecPipe.MULDIV_PIPE if s.func7_ == 0b1 else ExecPipe.ALU_PIPE
      if s.func3_ == 0b000 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_ADD
      elif s.func3_ == 0b000 and s.func7_ == 0b0100000:
        s.uop_op_.v = MicroOp.UOP_SUB
      elif s.func3_ == 0b001 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SLL
      elif s.func3_ == 0b010 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SLT
      elif s.func3_ == 0b011 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SLTU
      elif s.func3_ == 0b100 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_XOR
      elif s.func3_ == 0b101 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_SRL
      elif s.func3_ == 0b101 and s.func7_ == 0b0100000:
        s.uop_op_.v = MicroOp.UOP_SRA
      elif s.func3_ == 0b110 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_OR
      elif s.func3_ == 0b111 and s.func7_ == 0:
        s.uop_op_.v = MicroOp.UOP_AND
      elif s.func3_ == 0b000 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MUL
      elif s.func3_ == 0b001 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MULH
      elif s.func3_ == 0b010 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MULHSU
      elif s.func3_ == 0b011 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_MULHU
      elif s.func3_ == 0b100 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_DIV
      elif s.func3_ == 0b101 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_DIVU
      elif s.func3_ == 0b110 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_REM
      elif s.func3_ == 0b111 and s.func7_ == 0b1:
        s.uop_op_.v = MicroOp.UOP_REMU
      else:  # Illegal
        s.uop_op_.v = 0
        s.dec_op_fail_.v = 1

    @s.combinational
    def decode_load():
      s.dec_load_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_load_.v = MicroOp.UOP_LB
      elif s.func3_ == 0b001:
        s.uop_load_.v = MicroOp.UOP_LH
      elif s.func3_ == 0b010:
        s.uop_load_.v = MicroOp.UOP_LW
      elif s.func3_ == 0b011:
        s.uop_load_.v = MicroOp.UOP_LD
      elif s.func3_ == 0b100:
        s.uop_load_.v = MicroOp.UOP_LBU
      elif s.func3_ == 0b101:
        s.uop_load_.v = MicroOp.UOP_LHU
      elif s.func3_ == 0b110:
        s.uop_load_.v = MicroOp.UOP_LWU
      else:  # Illegal
        s.uop_load_.v = 0
        s.dec_load_fail_.v = 1

    @s.combinational
    def decode_store():
      s.dec_store_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_store_.v = MicroOp.UOP_SB
      elif s.func3_ == 0b001:
        s.uop_store_.v = MicroOp.UOP_SH
      elif s.func3_ == 0b010:
        s.uop_store_.v = MicroOp.UOP_SW
      elif s.func3_ == 0b011:
        s.uop_store_.v = MicroOp.UOP_SD
      else:  # Illegal
        s.uop_store_.v = 0
        s.dec_store_fail_.v = 1

    @s.combinational
    def decode_branch():
      s.dec_branch_fail_.v = 0
      if s.func3_ == 0b000:
        s.uop_branch_.v = MicroOp.UOP_BEQ
      elif s.func3_ == 0b001:
        s.uop_branch_.v = MicroOp.UOP_BNE
      if s.func3_ == 0b100:
        s.uop_branch_.v = MicroOp.UOP_BLT
      if s.func3_ == 0b101:
        s.uop_branch_.v = MicroOp.UOP_BGE
      if s.func3_ == 0b110:
        s.uop_branch_.v = MicroOp.UOP_BLTU
      if s.func3_ == 0b111:
        s.uop_branch_.v = MicroOp.UOP_BGEU
      else:  # Illegal
        s.uop_branch_.v = 0
        s.dec_branch_fail_.v = 1

    @s.combinational
    def decode_system():
      s.dec_system_fail_.v = 0
      if s.imm_i_ == 0 and s.rs1_ == 0 and s.func3_ == 0 and s.rd_ == 0:
        s.uop_system_.v = MicroOp.UOP_ECALL
      elif s.imm_i_ == 0b1 and s.rs1_ == 0 and s.func3_ == 0 and s.rs2_ == 0:
        s.uop_system_.v = MicroOp.UOP_EBREAK
      elif s.func3_ == 0b001:
        s.uop_system_.v = MicroOp.UOP_CSRRW
      elif s.func3_ == 0b010:
        s.uop_system_.v = MicroOp.UOP_CSRRS
      elif s.func3_ == 0b011:
        s.uop_system_.v = MicroOp.UOP_CSRRC
      elif s.func3_ == 0b101:
        s.uop_system_.v = MicroOp.UOP_CSRRWI
      elif s.func3_ == 0b110:
        s.uop_system_.v = MicroOp.UOP_CSRRSI
      elif s.func3_ == 0b111:
        s.uop_system_.v = MicroOp.UOP_CSRRCI
      else:  # Illegal
        s.uop_system_.v = 0
        s.dec_system_fail_.v = 1

    @s.combinational
    def decode_misc_mem():
      s.dec_misc_mem_fail_.v = 0
      if s.fence_upper_ == 0 and s.rs1_ == 0 and s.func3_ == 0 and s.rd_ == 0:
        s.uop_misc_mem_.v = MicroOp.UOP_FENCE
      elif s.imm_i_ == 0 and s.rs1_ == 0 and s.func3_ == 0b001 and s.rd_ == 0:
        s.uop_misc_mem_.v = MicroOp.UOP_FENCE_I
      else:  # Illegal
        s.uop_misc_mem_.v = 0
        s.dec_misc_mem_fail_.v = 1

    @s.tick_rtl
    def update_out():
      if s.accepted_:
        s.decmsg_.n = s.dec_

  def line_trace(s):
    return str(s.decmsg_)
