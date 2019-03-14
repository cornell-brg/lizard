from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.comparator import Comparator, ComparatorInterface
from util.rtl.register import Register, RegisterInterface
from bitutil import clog2, clog2nz
from core.rtl.messages import DispatchMsg, ExecuteMsg, AluMsg, AluFunc


class BranchInterface(Interface):

  def __init__(s, data_len):
    s.DataLen = data_len
    super(BranchInterface, s).__init__([
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


class Branch(Model):

  def __init__(s, branch_interface):
    UseInterface(s, branch_interface)
    imm_len = DispatchMsg().imm.nbits
    data_len = s.interface.DataLen
    spec_idx_len = DispatchMsg().hdr_spec.nbits

    s.require(
        MethodSpec(
            'dispatch_get',
            args=None,
            rets={'msg': DispatchMsg()},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'cflow_redirect',
            args={
                'spec_idx': Bits(spec_idx_len),
                'target': Bits(data_len),
                'force': Bits(1),
            },
            rets={},
            call=True,
            rdy=False,
        ),
    )

    s.out_val_ = Register(RegisterInterface(Bits(1)), reset_value=0)
    s.out_ = Register(RegisterInterface(ExecuteMsg(), enable=True))

    s.cmp_ = Comparator(ComparatorInterface(data_len))
    s.accepted_ = Wire(1)
    s.msg_ = Wire(DispatchMsg())
    s.msg_imm_ = Wire(imm_len)
    s.imm_ = Wire(data_len)

    s.take_branch_ = Wire(1)
    s.branch_target_ = Wire(data_len)

    # Connect to disptach get method
    s.connect(s.msg_, s.dispatch_get_msg)
    s.connect(s.dispatch_get_call, s.accepted_)

    # Connect to registers
    s.connect(s.out_.write_call, s.accepted_)

    # Connect up cmp call
    # s.connect(s.cmp_.exec_src0, TODO)
    # s.connect(s.cmp_.exec_src1, TODO)
    # s.connect(s.cmp_.exec_unsigned, TODO)
    s.connect(s.cmp_.exec_call, s.accepted_)

    # Connect get call
    s.connect(s.peek_msg, s.out_.read_data)
    s.connect(s.peek_rdy, s.out_val_.read_data)

    # Connect up to controlflow redirect method
    s.connect(s.cflow_redirect_spec_idx, s.msg_.hdr_spec)
    s.connect(s.cflow_redirect_target, s.branch_target_)
    s.connect(s.cflow_redirect_force, 0)
    s.connect(s.cflow_redirect_call, s.accepted_)

    @s.combinational
    def set_take_branch():
      s.take_branch_.v = 0
      # TODO handle branches that are not conditional
      s.take_branch_.v = s.cmp_.exec_res

    @s.combinational
    def set_valid():
      s.out_val_.write_data.v = s.accepted_ or (s.out_val_.read_data and
                                                not s.take_call)

    @s.combinational
    def set_accepted():
      s.accepted_.v = (s.take_call or not s.out_val_.read_data
                      ) and s.cmp_.exec_rdy and s.dispatch_get_rdy

    @s.combinational
    def set_inputs():
      # TODO set the proper compare function
      s.cmp_.exec_func.v = 0

    @s.combinational
    def compute_target():
      s.msg_imm_.v = s.msg_.imm
      # PYMTL_BROKEN: sext(s.msg_.imm) does not create valid verilog
      # Vivado errors: "range is not allowed in prefix"
      s.imm_.v = sext(s.msg_imm_, data_len)
      if s.take_branch_:
        s.branch_target_.v = s.msg_.hdr_pc + s.imm_
      else:
        s.branch_target_.v = s.msg_.hdr_pc + 4

    @s.combinational
    def set_value_reg_input():
      s.out_.write_data.v = 0
      s.out_.write_data.hdr.v = s.msg_.hdr
