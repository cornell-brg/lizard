from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl import alu
from util.rtl.register import Register, RegisterInterface
from util.rtl.lookup_table import LookupTable, LookupTableInterface
from bitutil import clog2, clog2nz
from core.rtl.messages import DispatchMsg, ExecuteMsg, AluMsg, AluFunc


class ALUInterface(Interface):

  def __init__(s, data_len):
    s.DataLen = data_len
    super(ALUInterface, s).__init__([
        MethodSpec(
            'peek',
            args=None,
            rets={
                'msg': ExecuteMsg(),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'take',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
    ])


class ALU(Model):

  def __init__(s, alu_interface):
    UseInterface(s, alu_interface)
    s.require(
        MethodSpec(
            'dispatch_get',
            args=None,
            rets={'msg': DispatchMsg()},
            call=True,
            rdy=True,
        ),)

    imm_len = DispatchMsg().imm.nbits
    data_len = s.interface.DataLen

    OP_LUT_MAP = {
        AluFunc.ALU_FUNC_ADD: alu.ALUFunc.ALU_ADD,
        AluFunc.ALU_FUNC_SUB: alu.ALUFunc.ALU_SUB,
        AluFunc.ALU_FUNC_AND: alu.ALUFunc.ALU_AND,
        AluFunc.ALU_FUNC_OR: alu.ALUFunc.ALU_OR,
        AluFunc.ALU_FUNC_XOR: alu.ALUFunc.ALU_XOR,
        AluFunc.ALU_FUNC_SLL: alu.ALUFunc.ALU_SLL,
        AluFunc.ALU_FUNC_SRL: alu.ALUFunc.ALU_SRL,
        AluFunc.ALU_FUNC_SRA: alu.ALUFunc.ALU_SRA,
        AluFunc.ALU_FUNC_SLT: alu.ALUFunc.ALU_SLT,
        AluFunc.ALU_FUNC_AUIPC:
            alu.ALUFunc.ALU_ADD,  # We are just adding to the PC
        AluFunc.ALU_FUNC_LUI: alu.ALUFunc.ALU_OR,
    }

    s.out_val_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.out_ = Register(RegisterInterface(ExecuteMsg(), enable=True))
    s.op_lut_ = LookupTable(
        LookupTableInterface(DispatchMsg().alu_msg_func.nbits,
                             alu.ALUFunc.bits), OP_LUT_MAP)

    s.alu_ = alu.ALU(alu.ALUInterface(data_len))
    s.accepted_ = Wire(1)
    s.msg_ = Wire(DispatchMsg())
    s.msg_imm_ = Wire(imm_len)

    # PYMTL_BROKEN, cant do msg.src1[:32]
    s.src1_ = Wire(data_len)
    s.src1_32_ = Wire(32)
    s.src2_ = Wire(data_len)
    s.src2_32_ = Wire(32)
    s.imm_ = Wire(data_len)
    s.imm_l20_ = Wire(data_len)

    s.res_ = Wire(data_len)
    s.res_32_ = Wire(32)

    # Connect up lookup table
    s.connect(s.op_lut_.lookup_in_, s.msg_.alu_msg_func)
    s.connect(s.alu_.exec_func, s.op_lut_.lookup_out)

    # Connect to disptach get method
    s.connect(s.msg_, s.dispatch_get_msg)
    s.connect(s.dispatch_get_call, s.accepted_)

    # Connect to registers
    s.connect(s.out_.write_call, s.accepted_)

    # Connect up alu call
    s.connect(s.alu_.exec_unsigned, s.msg_.alu_msg_unsigned)
    s.connect(s.alu_.exec_call, s.accepted_)

    # Connect get call
    s.connect(s.peek_msg, s.out_.read_data)
    s.connect(s.peek_rdy, s.out_val_.read_data)

    @s.combinational
    def set_valid():
      s.out_val_.write_data.v = s.accepted_ or (s.out_val_.read_data and
                                                not s.take_call)

    @s.combinational
    def set_accepted():
      s.accepted_.v = (s.take_call or not s.out_val_.read_data
                      ) and s.alu_.exec_rdy and s.dispatch_get_rdy

    # PYMTL_BROKEN
    s.rs1_ = Wire(data_len)
    s.rs2_ = Wire(data_len)
    s.res_ = Wire(data_len)
    s.res_trunc_ = Wire(data_len)
    s.connect_wire(s.rs1_, s.msg_.rs1)
    s.connect_wire(s.rs2_, s.msg_.rs2)
    s.connect(s.res_, s.alu_.exec_res)

    @s.combinational
    def slice32():
      s.src1_32_.v = s.rs1_[:32]
      s.src2_32_.v = s.rs2_[:32]
      s.res_32_.v = s.res_[:32]

    @s.combinational
    def set_src_res():
      if s.msg_.alu_msg_op32:
        s.src1_.v = zext(s.src1_32_,
                         data_len) if s.msg_.alu_msg_unsigned else sext(
                             s.src1_32_, data_len)
        s.src2_.v = zext(s.src2_32_,
                         data_len) if s.msg_.alu_msg_unsigned else sext(
                             s.src2_32_, data_len)
        s.res_trunc_.v = zext(s.res_32_,
                              data_len) if s.msg_.alu_msg_unsigned else sext(
                                  s.res_32_, data_len)
      else:
        s.src1_.v = s.rs1_
        s.src2_.v = s.rs2_
        s.res_trunc_.v = s.res_
        if s.msg_.alu_msg_func == AluFunc.ALU_FUNC_AUIPC:
          s.src1_.v = s.msg_.hdr_pc
        elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_LUI:  # LUI is a special case
          s.src1_.v = 0

    @s.combinational
    def set_inputs():
      # PYMTL_BROKEN: sext, concat, and zext only work with wires and constants
      s.msg_imm_.v = s.msg_.imm
      s.imm_.v = sext(s.msg_imm_, data_len)
      if s.msg_.alu_msg_func == AluFunc.ALU_FUNC_AUIPC or s.msg_.alu_msg_func == AluFunc.ALU_FUNC_LUI:
        s.imm_.v = s.imm_ << 12
      s.alu_.exec_src0.v = s.src1_
      s.alu_.exec_src1.v = s.src2_ if s.msg_.rs2_val else s.imm_

    @s.combinational
    def set_value_reg_input():
      s.out_.write_data.v = 0
      s.out_.write_data.hdr.v = s.msg_.hdr
      s.out_.write_data.result.v = s.res_trunc_
      s.out_.write_data.rd.v = s.msg_.rd
      s.out_.write_data.rd_val.v = s.msg_.rd_val
