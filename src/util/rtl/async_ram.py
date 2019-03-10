from pymtl import *
from bitutil import clog2, clog2nz
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type


class AsynchronousRAMInterface(Interface):

  def __init__(s,
               dtype,
               nwords,
               num_read_ports,
               num_write_ports,
               write_read_bypass=False):
    s.Addr = Bits(clog2nz(nwords))
    s.Data = canonicalize_type(dtype)
    s.Bypass = write_read_bypass
    s.NumWords = nwords

    ordering_chains = [
        s.bypass_chain('write', 'read', write_read_bypass),
    ]

    super(AsynchronousRAMInterface, s).__init__(
        [
            MethodSpec(
                'read',
                args={
                    'addr': s.Addr,
                },
                rets={
                    'data': s.Data,
                },
                call=False,
                rdy=False,
                count=num_read_ports),
            MethodSpec(
                'write',
                args={
                    'addr': s.Addr,
                    'data': s.Data,
                },
                rets=None,
                call=True,
                rdy=False,
                count=num_write_ports),
        ],
        ordering_chains=ordering_chains,
    )


# https://people.ece.cornell.edu/land/courses/ece5760/DE1_SOC/HDL_style_qts_qii51007.pdf
# Thanks Bruce Land, See 12-12
class AsynchronousRAM(Model):

  def __init__(s, interface, reset_values=None):
    UseInterface(s, interface)
    nwords = s.interface.NumWords
    num_read_ports = len(s.read_data)
    num_write_ports = len(s.write_data)
    # The core ram
    s.regs = [Wire(s.interface.Data) for _ in range(nwords)]

    # combinational read block
    if s.interface.Bypass:

      @s.combinational
      def handle_reads():
        for i in range(num_read_ports):
          s.read_data[i].v = s.regs[s.read_addr[i]]
          # Bypass logic
          for j in range(num_write_ports):
            if s.write_call[j] and s.write_addr[j] == s.read_addr[i]:
              s.read_data[i].v = s.write_data[j]
    else:

      @s.combinational
      def handle_reads():
        for i in range(num_read_ports):
          s.read_data[i].v = s.regs[s.read_addr[i]]

    # Sequential write  block
    if reset_values is None:  # No reset value

      @s.tick_rtl
      def handle_writes():
        for i in range(num_write_ports):
          if s.write_call[i]:
            s.regs[s.write_addr[i]].n = s.write_data[i]
    elif isinstance(reset_values, list):  # A list of reset values
      assert len(reset_values) == nwords
      # Need to lift constants into wire signals
      s.reset_values = [Wire(s.interface.Data) for _ in range(nwords)]
      for i in range(nwords):
        s.connect(s.reset_values[i], int(reset_values[i]))

      @s.tick_rtl
      def handle_writes():
        if s.reset:
          for i in range(nwords):
            s.regs[i].n = s.reset_values[i]
        else:
          for i in range(num_write_ports):
            if s.write_call[i]:
              s.regs[s.write_addr[i]].n = s.write_data[i]
    else:  # Constant reset value

      @s.tick_rtl
      def handle_writes():
        if s.reset:
          for i in range(nwords):
            s.regs[i].n = reset_values
        else:
          for i in range(num_write_ports):
            if s.write_call[i]:
              s.regs[s.write_addr[i]].n = s.write_data[i]

  def line_trace(s):
    return ":".join(["{}".format(x) for x in s.regs])
