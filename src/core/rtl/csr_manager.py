from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.messages import CsrFunc
from msg.codes import CsrRegisters
from config.general import CSR_SPEC_NBITS, XLEN
from bitutil import bit_enum


class CSRManagerInterface(Interface):

  def __init__(s):
    super(CSRManagerInterface, s).__init__([
        MethodSpec(
            'op',
            args={
                'csr': Bits(CSR_SPEC_NBITS),
                'op': Bits(CsrFunc.bits),
                'rs1_is_x0': Bits(1),
                'value': Bits(XLEN),
            },
            rets={
                'old': Bits(XLEN),
                'success': Bits(1),
            },
            call=True,
            rdy=False,
        ),
    ])


class CSRManager(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    s.require(
        MethodSpec(
            'debug_recv',
            args=None,
            rets={'msg': Bits(XLEN)},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'debug_send',
            args={'msg': Bits(XLEN)},
            rets=None,
            call=True,
            rdy=True,
        ),
    )

    # PYMTL_BROKEN
    s.temp_debug_recv_call = Wire(1)
    s.temp_debug_send_call = Wire(1)
    s.temp_debug_send_msg = Wire(Bits(XLEN))
    s.temp_op_success = Wire(1)
    s.temp_op_old = Wire(Bits(XLEN))

    @s.combinational
    def handle_op():
      s.temp_debug_recv_call.v = 0

      s.temp_debug_send_call.v = 0
      s.temp_debug_send_msg.v = 0

      s.temp_op_success.v = 0
      s.temp_op_old.v = 0

      if s.op_call:
        if s.op_csr == CsrRegisters.proc2mngr:
          if s.op_op == CsrFunc.CSR_FUNC_READ_WRITE and s.debug_send_rdy:
            s.temp_debug_send_call.v = 1
            s.temp_debug_send_msg.v = s.op_value

            s.temp_op_success.v = 1
            s.temp_op_old.v = 0
        elif s.op_csr == CsrRegisters.mngr2proc:
          if s.op_op != CsrFunc.CSR_FUNC_READ_WRITE and s.debug_recv_rdy and s.op_rs1_is_x0:
            s.temp_debug_recv_call.v = 1

            s.temp_op_success.v = 1
            s.temp_op_old.v = s.debug_recv_msg

      s.debug_recv_call.v = s.temp_debug_recv_call
      s.debug_send_call.v = s.temp_debug_send_call
      s.debug_send_msg.v = s.temp_debug_send_msg
      s.op_success.v = s.temp_op_success
      s.op_old.v = s.temp_op_old
