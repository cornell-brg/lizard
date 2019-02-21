from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from core.rtl.frontend.imm_decoder import ImmType

from config.general import ILEN


class SubDecoderInterface(Interface):

  def __init__(s, Kind):
    super(SubDecoderInterface, s).__init__([
        MethodSpec(
            'decode',
            args={
                'inst': Bits(ILEN),
            },
            rets={
                'success': Bits(1),
                'rs1_valid': Bits(1),
                'rs2_valid': Bits(1),
                'rd_valid': Bits(1),
                'imm_type': Bits(ImmType.bits),
                'imm_valid': Bits(1),
                'result': Kind,
            },
            call=False,
            rdy=False,
        ),
    ])
