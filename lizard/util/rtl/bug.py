from pymtl import *
from lizard.util.rtl.method import MethodSpec
from lizard.bitutil import clog2, clog2nz


class BugInterface:

  def __init__(s):
    s.Out = Bits(2)

    s.port = MethodSpec({
        'select': Bits(1),
    }, {
        'out': s.Out,
    }, False, False)


class Bug(Model):

  def __init__(s):
    s.interface = BugInterface()
    s.port = s.interface.port.in_port()

    s.outs = [Wire(2) for _ in range(2)]

    @s.combinational
    def compute_1():
      s.outs[0].v = 1

    @s.combinational
    def compute_2():
      if s.port.select:
        s.outs[1].v = 3
      else:
        s.outs[1].v = s.outs[0].v

    @s.combinational
    def compute_3():
      s.port.out.v = s.outs[1]

  def line_trace(s):
    return "{}".format(s.port.out)


class BugMagic(Model):

  def __init__(s):
    s.interface = BugInterface()
    s.port = s.interface.port.in_port()

    s.outs = [Wire(2) for _ in range(2)]
    s.constone = Wire(2)
    s.connect(s.constone, 1)

    @s.combinational
    def compute_1():
      s.outs[0].v = s.constone

    @s.combinational
    def compute_2():
      if s.port.select:
        s.outs[1].v = 3
      else:
        s.outs[1].v = s.outs[0].v

    @s.combinational
    def compute_3():
      s.port.out.v = s.outs[1]

  def line_trace(s):
    return "{}".format(s.port.out)


class Helper(Model):

  def __init__(s):
    s.interface = BugInterface()
    s.port = s.interface.port.in_port()

    @s.combinational
    def handle_bit_0():
      s.port.out[0].v = (s.port.select == 0)

    @s.combinational
    def handle_bit_1():
      s.port.out[1].v = (s.port.select == 1)


class Bug2(Model):

  def __init__(s):
    s.interface = BugInterface()
    s.port = s.interface.port.in_port()

    s.helper = Helper()

    s.connect(s.helper.port.select, s.port.select)

    @s.combinational
    def invert():
      s.port.out.v = ~s.helper.port.out
