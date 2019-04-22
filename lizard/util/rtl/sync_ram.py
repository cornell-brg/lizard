from pymtl import *
from lizard.bitutil import clog2, clog2nz
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import Array, canonicalize_type


class SynchronousRAMInterface(Interface):

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

    super(SynchronousRAMInterface, s).__init__(
        [
            MethodSpec(
                'read_next',
                args={
                    'addr': s.Addr,
                },
                call=False,
                rdy=False,
                count=num_read_ports),
            MethodSpec(
                'read',
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
class SynchronousRAM(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    nwords = s.interface.NumWords
    num_read_ports = len(s.read_data)
    num_write_ports = len(s.write_data)
    # The core ram
    s.regs = [Wire(s.interface.Data) for _ in range(nwords)]

    if s.interface.Bypass:

      @s.tick_rtl
      def handle_writes():
        for i in range(num_write_ports):
          if s.write_call[i]:
            s.regs[s.write_addr[i]].v = s.write_data[i]

        for i in range(num_read_ports):
          s.read_data[i].v = s.regs[s.read_next_addr[i]]
    else:

      @s.tick_rtl
      def handle_writes():
        for i in range(num_write_ports):
          if s.write_call[i]:
            s.regs[s.write_addr[i]].n = s.write_data[i]

        for i in range(num_read_ports):
          s.read_data[i].n = s.regs[s.read_next_addr[i]]

  def line_trace(s):
    return ":".join(["{}".format(x) for x in s.regs])
