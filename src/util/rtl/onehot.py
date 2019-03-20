from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil import clog2, clog2nz


class OneHotEncoderInterface(Interface):

  def __init__(s, noutbits, enable=False):
    s.Out = Bits(noutbits)
    s.In = clog2nz(noutbits)
    s.En = enable
    super(OneHotEncoderInterface, s).__init__([
        MethodSpec(
            'encode',
            args={
                'number': s.In,
            },
            rets={
                'onehot': s.Out,
            },
            call=enable,
            rdy=False),
    ])


class OneHotEncoder(Model):

  def __init__(s, noutbits, enable=False):
    UseInterface(s, OneHotEncoderInterface(noutbits, enable))

    for i in range(noutbits):

      if s.interface.En:

        @s.combinational
        def handle_encode(i=i):
          s.encode_onehot[i].v = s.encode_call and (s.encode_number == i)
      else:

        @s.combinational
        def handle_encode(i=i):
          s.encode_onehot[i].v = (s.encode_number == i)

  def line_trace(s):
    return "i: {} o: {}".format(s.encode_number, s.encode_onehot)
