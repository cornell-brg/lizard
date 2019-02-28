from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl import alu
from util.rtl.register import Register, RegisterInterface
from bitutil import clog2, clog2nz
from core.rtl.messages import DispatchMsg, ExecuteMsg, AluMsg, AluFunc

class ALUInterface(Interface):

  def __init__(s, data_len):
    s.DataLen = data_len
    super(ALUInterface, s).__init__([
        MethodSpec(
            'get',
            args=None,
            rets={
                'msg': ExecuteMsg(),
            },
            call=True,
            rdy=True,
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
      ),
    )

    imm_len = DispatchMsg().imm.nbits
    data_len = s.interface.DataLen

    s.out_val_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.out_ = Register(RegisterInterface(ExecuteMsg(), enable=True))

    s.alu_ = alu.ALU(alu.ALUInterface(data_len))
    s.accepted_ = Wire(1)
    s.msg_ = Wire(DispatchMsg())

    # PYMTL_BROKEN, cant do msg.src1[:32]
    s.src1_ = Wire(data_len)
    s.src1_32_ = Wire(32)
    s.src2_ = Wire(data_len)
    s.src2_32_ = Wire(32)
    s.imm_ = Wire(data_len)

    s.res_ = Wire(data_len)
    s.res_32_ = Wire(32)

    # Connect to disptach get method
    s.connect(s.msg_, s.dispatch_get_msg)
    s.connect(s.dispatch_get_call, s.accepted_)

    # Connect to registers
    s.connect(s.out_.write_call, s.accepted_)

    # Connect up alu call
    s.connect(s.alu_.exec_unsigned, s.msg_.alu_msg_unsigned)
    s.connect(s.alu_.exec_call, s.accepted_)

    # Connect get call
    s.connect(s.get_msg, s.out_.read_data)
    s.connect(s.get_rdy, s.out_val_.read_data)

    @s.combinational
    def set_valid():
      s.out_val_.write_data.v = s.accepted_ or (s.out_val_.read_data and not s.get_call)

    @s.combinational
    def set_accepted():
      s.accepted_.v = (s.get_call or not s.out_val_.read_data) and s.alu_.exec_rdy and s.dispatch_get_rdy

    @s.combinational
    def set_src_res():
      s.src1_32_.v = s.msg_.rs1[:32]
      s.src2_32_.v = s.msg_.rs2[:32]
      s.res_32_.v = s.alu_.exec_res[:32]

      if s.msg_.alu_msg_op32:
        s.src1_.v = zext(s.src1_32_, data_len) if s.msg_.alu_msg_unsigned else sext(s.src1_32_, data_len)
        s.src2_.v = zext(s.src2_32_, data_len) if s.msg_.alu_msg_unsigned else sext(s.src2_32_, data_len)
        s.res_.v = zext(s.res_32_, data_len) if s.msg_.alu_msg_unsigned else sext(s.res_32_, data_len)
      else:
        s.src1_.v = s.msg_.rs1
        s.src2_.v = s.msg_.rs2
        s.res_.v = s.alu_.exec_res


    @s.combinational
    def set_inputs():
      s.imm_.v = sext(s.msg_.imm, data_len)
      # TODO handle LUI and AUIPC
      s.alu_.exec_src0.v = s.src1_
      s.alu_.exec_src1.v = s.src2_ if s.msg_.rs2_val else s.imm_
      # Set the function
      s.alu_.exec_func.v = 0
      if s.msg_.alu_msg_func == AluFunc.ALU_FUNC_ADD:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_ADD
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_SUB:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_SUB
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_AND:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_AND
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_OR:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_OR
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_XOR:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_XOR
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_SLL:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_SLL
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_SRL:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_SRL
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_SRA:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_SRA
      elif s.msg_.alu_msg_func == AluFunc.ALU_FUNC_SLT:
        s.alu_.exec_func.v = alu.ALUFunc.ALU_SLT

    @s.combinational
    def set_value_reg_input():
      s.out_.write_data.v = 0
      s.out_.write_data.hdr.v = s.msg_.hdr
      s.out_.write_data.result.v = s.res_
      s.out_.write_data.rd.v = s.msg_.rd
