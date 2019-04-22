from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import Array, canonicalize_type
from lizard.bitutil import clog2, clog2nz


class MuxInterface(Interface):

  def __init__(s, dtype, nports):
    s.Data = canonicalize_type(dtype)
    s.Select = Bits(clog2nz(nports))

    super(MuxInterface, s).__init__([
        MethodSpec(
            'mux',
            args={
                'in_': Array(s.Data, nports),
                'select': s.Select,
            },
            rets={
                'out': s.Data,
            },
            call=False,
            rdy=False,
        ),
    ])


class Mux(Model):
  """A multiplexer.
  
  Parameters:
    dtype: the datatype of the inputs and the output
    nports: the number of input ports to choose from

  Methods:
    mux:
      performs the muxing function. No call, always ready.
      Inputs:
        in (s.Data[nports]): the inputs.
        select (s.Select): the select signal. The width is clog2(nports).
          If there is only 1 input, the select signal is 1 bit wide, and must be 0.
      Outputs:
        out (s.Data): the output data, of type dtype.

  Sequencing:
    Data from in read before the mux function is computed.
  """

  def __init__(s, dtype, nports):
    UseInterface(s, MuxInterface(dtype, nports))

    @s.combinational
    def select():
      assert s.mux_select < nports
      s.mux_out.v = s.mux_in_[s.mux_select]

  def line_trace(s):
    return "[{}][{}]: {}".format(', '.join([str(x) for x in s.mux_in_]),
                                 s.mux_select, s.mux_out)
