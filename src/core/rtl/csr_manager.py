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

  def __init__(s, interface, proc_debug_bus_interface):
    UseInterface(s, interface)

    proc_debug_bus_interface.require(s, '', 'recv')
    proc_debug_bus_interface.require(s, '', 'send')

    @s.combinational
    def handle_op():
      s.recv_call.v = 0

      s.send_call.v = 0
      s.send_msg.v = 0

      s.op_success.v = 0
      s.op_old.v = 0

      if s.op_call:
        if s.csr == CsrRegisters.proc2mngr:
          if s.op_op == CSROpType.READ_WRITE and s.send_rdy:
            s.send_call.v = 1
            s.send_msg.v = s.op_value

            s.op_success.v = 1
            s.op_old.v = 0
        elif s.csr == CsrRegisters.mngr2proc:
          if s.op_op != CSROpType.READ_WRITE and s.recv_rdy and s.op_rs1_is_x0:
            s.recv_call.v = 1

            s.op_success.v = 1
            s.op_old.v = s.recv_msg
