from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from msg.codes import CsrRegisters
from config.general import CSR_SPEC_NBITS, XLEN
from bitutil import bit_enum

CSROpType = bit_enum(
    'CSROpType',
    None,
    ('READ_WRITE', 'rw'),
    ('READ_SET', 'rs'),
    ('READ_CLEAR', 'rc'),
)


class CSRManagerInterface(Interface):

  def __init__(s):
    super(CSRManagerInterface, s).__init__([
        MethodSpec(
            'op',
            args={
                'csr': Bits(CSR_SPEC_NBITS),
                'op': Bits(CSROpType.bits),
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

    @s.combinational
    def handle_op():
      s.debug_recv_call.v = 0

      s.debug_send_call.v = 0
      s.debug_send_msg.v = 0

      s.op_success.v = 0
      s.op_old.v = 0

      if s.op_call:
        if s.op_csr == CsrRegisters.proc2mngr:
          if s.op_op == CSROpType.READ_WRITE and s.debug_send_rdy:
            s.debug_send_call.v = 1
            s.debug_send_msg.v = s.op_value

            s.op_success.v = 1
            s.op_old.v = 0
        elif s.op_csr == CsrRegisters.mngr2proc:
          if s.op_op != CSROpType.READ_WRITE and s.debug_recv_rdy and s.op_rs1_is_x0:
            s.debug_recv_call.v = 1

            s.op_success.v = 1
            s.op_old.v = s.debug_recv_msg
