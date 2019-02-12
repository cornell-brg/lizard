from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl import alu
from core.rtl.controlflow import ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.messages import DispatchMsg
from msg.codes import RVInstMask, Opcode, ExceptionCode
from core.rtl.frontend.decode import DecodeInterface
from core.rtl.micro_op import MicroOp


class ALUInterface(Interface):

  def __init__(s, data_len, imm_len):
    s.DataLen = data_len
    s.ImmLen = imm_len
    super(ALUInterface, s).__init__(
        [],
        ordering_chains=[
            [],
        ],
    )


class ALU(Model):

  def __init__(s, alu_interface):
    UseInterface(s, alu_interface)
    data_len = alu_interface.DataLen
    imm_len = alu_interface.ImmLen

    s.alu_interface_ = alu.ALUInterface(data_len)
    s.alu_ = alu.ALU(s.alu_interface_)
    # Import the execute method
    s.alu_interface_.require(s, 'alu', 'exec')

    s.rdy_ = Wire(1)
    s.accepted_ = Wire(1)
    s.msg_ = Wire(DispatchMsg())

    s.connect(s.msg_, 0x0)

    # PYMTL_BROKEN, cant do msg.src1[:32]
    s.src1_ = Wire(data_len)
    s.src1_32_ = Wire(32)
    s.src2_ = Wire(data_len)
    s.src2_32_ = Wire(32)
    s.imm_ = Wire(imm_len)
    s.connect_wire(s.imm_, s.msg_.imm)
    s.uop_ = Wire(s.msg_.uop.nbits)
    s.connect_wire(s.uop_, s.msg_.uop)

    s.res_ = Wire(data_len)
    s.res_32_ = Wire(32)
    # Connect up ALU
    s.connect(s.alu_exec_src0, s.src1_)
    s.connect(s.alu_exec_src1, s.src2_)

    uop_32s = [
        MicroOp.UOP_ADDIW, MicroOp.UOP_SLLIW, MicroOp.UOP_SRLIW,
        MicroOp.UOP_SRAIW, MicroOp.UOP_ADDW, MicroOp.UOP_SUBW, MicroOp.UOP_SLLW,
        MicroOp.UOP_SRLW, MicroOp.UOP_SRAW
    ]
    #
    #
    # @s.combinational
    # def set_op32(i=i):

    @s.combinational
    def set_ops():
      # PYMTL_BROKEN sext(foo[x:y]) does not work if foo is bitstruct
      s.src1_ = s.msg_.src1
      s.src2_ = s.msg_.src2
      if s.accepted_:
        s.src1_.v = s.src1_ if not s.msg_.op32 else sext(s.src1_32_, data_len)
        s.src2_.v = s.src2_ if not s.msg_.op32 else sext(s.src2_32_, data_len)
        if s.msg_.imm_val:  # Replace src2 with imm
          if s.uop_ == MicroOp.UOP_LUI:
            s.src2_.v = sext(s.imm_, data_len) << 12
          elif s.uop_ == MicroOp.UOP_AUIPC:
            s.src1_.v = s.msg_.pc
            s.src2_.v = sext(s.imm_, data_len) << 12
          else:
            s.src2_.v = sext(s.imm_, data_len)

      s.src1_32_.v = s.src1_[:32]
      s.src2_32_.v = s.src2_[:32]

    @s.combinational
    def set_res():
      s.res_32_.v = s.alu_exec_res[:32]
      s.res_.v = s.alu_exec_res if not s.msg_.op32 else sext(
          s.res_32_, data_len)

    @s.combinational
    def set_rdy():
      # TODO, fill these out
      s.rdy_.v = 1
      s.accepted_.v = 1
