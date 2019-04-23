from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.thermometer_mask import ThermometerMask, ThermometerMaskInterface
from lizard.bitutil import clog2


class ArbiterInterface(Interface):

  def __init__(s, nreqs):
    s.nreqs = nreqs
    super(ArbiterInterface, s).__init__([
        MethodSpec(
            'grant',
            args={
                'reqs': Bits(nreqs),
            },
            rets={
                'grant': Bits(nreqs),
            },
            call=False,
            rdy=False,
        ),
    ])


# Based on design from: http://fpgacpu.ca/fpga/priority.html
class PriorityArbiter(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    @s.combinational
    def compute():
      # PYMTL_BROKEN unary - translates but does not simulate
      s.grant_grant.v = s.grant_reqs & (0 - s.grant_reqs)

  def line_trace(s):
    return "{} -> {}".format(s.grant_reqs, s.grant_grant)


# Based on design from: http://fpgacpu.ca/fpga/roundrobin.html
# and "Arbiters: Design Ideas and Coding Styles" by Matt Weber,
# Silicon Logic Engineering, Inc.
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.86.550&rep=rep1&type=pdf
class RoundRobinArbiter(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    nreqs = s.interface.nreqs

    s.mask = Register(RegisterInterface(Bits(nreqs)), reset_value=0)
    s.masker = ThermometerMask(ThermometerMaskInterface(nreqs))
    s.raw_arb = PriorityArbiter(ArbiterInterface(nreqs))
    s.masked_arb = PriorityArbiter(ArbiterInterface(nreqs))
    s.final_grant = Wire(nreqs)

    s.connect(s.raw_arb.grant_reqs, s.grant_reqs)
    s.connect(s.masker.mask_in_, s.mask.read_data)

    @s.combinational
    def compute():
      s.masked_arb.grant_reqs.v = s.grant_reqs & s.masker.mask_out
      if s.masked_arb.grant_grant == 0:
        s.final_grant.v = s.raw_arb.grant_grant
      else:
        s.final_grant.v = s.masked_arb.grant_grant

    s.connect(s.mask.write_data, s.final_grant)
    s.connect(s.grant_grant, s.final_grant)

  def line_trace(s):
    return "{} -> {}".format(s.grant_reqs, s.grant_grant)
