from pymtl import *

from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from config.general import *


class InstrState(BitStructDefinition):

  def __init__(s):
    s.succesor_pc = BitField(XLEN)
    s.valid = BitField(1)
    s.in_flight = BitField(1)
    s.rename_table_snapshot_id = BitField(MAX_SPEC_DEPTH_NBITS)
    s.has_rename_snapshot = BitField(1)

  def __str__(s):
    return 'spc: {} v: {} f: {} s: {}:{}'.format(
        s.succesor_pc, s.valid, s.in_flight, s.has_rename_snapshot,
        s.rename_table_snapshot_id)

  def __repr__(s):
    return str(s)



class ControlFlowManagerInterface(Interface):

  def __init__(s):
    super(ControlFlowManagerInterface, s).__init__(
        [
            MethodSpec(
                'check_redirect',
                args={},
                rets={
                    'redirect' : Bits(1),
                    'target': XLEN,
                },
                call=False,
                rdy=False,
            ),
        ],
        ordering_chains=[
          [],
        ],
    )


class ControlFlowManager(Model):

  def __init__(s):
    s.inter = ControlFlowManagerInterface()
    s.apply(s)
