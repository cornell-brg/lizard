from pymtl import *
from lizard.bitutil import clog2, clog2nz
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import Array, canonicalize_type
from lizard.util.rtl.async_ram import AsynchronousRAM, AsynchronousRAMInterface


class RegisterFileInterface(Interface):

  def __init__(s, dtype, nregs, num_read_ports, num_write_ports,
               write_read_bypass, write_dump_bypass):
    s.Addr = Bits(clog2nz(nregs))
    s.Data = canonicalize_type(dtype)

    ordering_chains = [
        s.bypass_chain('write', 'read', write_read_bypass),
        s.bypass_chain('write', 'dump', write_dump_bypass),
    ] + s.successor('set', ['read', 'write', 'dump'])

    super(RegisterFileInterface, s).__init__(
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
            MethodSpec(
                'dump',
                args=None,
                rets={
                    'out': Array(s.Data, nregs),
                },
                call=False,
                rdy=False,
            ),
            MethodSpec(
                'set',
                args={
                    'in_': Array(s.Data, nregs),
                },
                rets=None,
                call=True,
                rdy=False,
            ),
        ],
        ordering_chains=ordering_chains,
    )


class RegisterFile(Model):

  def __init__(s,
               dtype,
               nregs,
               num_read_ports,
               num_write_ports,
               write_read_bypass,
               write_dump_bypass,
               reset_values=None):
    UseInterface(
        s,
        RegisterFileInterface(dtype, nregs, num_read_ports, num_write_ports,
                              write_read_bypass, write_dump_bypass))

    # The core register file
    s.regs = [Wire(s.interface.Data) for _ in range(nregs)]
    # pymtl crashes when translating nested lists
    # https://github.com/cornell-brg/pymtl/issues/137
    # PYMTL_BROKEN workaround
    # Each layer below represents the register file after modification by 1
    # write port
    s.write_inc = [
        Wire(s.interface.Data) for _ in range(nregs * num_write_ports)
    ]
    # Contains the state of the register file after all writes have been processed
    s.after_write = [Wire(s.interface.Data) for _ in range(nregs)]
    s.after_set = [Wire(s.interface.Data) for _ in range(nregs)]

    if reset_values is None:
      reset_values = [0 for _ in range(nregs)]
    else:
      reset_values = [int(reset_value) for reset_value in reset_values]

    # Handle write, dump, and set (in that order)
    for reg_i in range(nregs):
      # Update each layer in write_inc
      for port in range(num_write_ports):

        @s.combinational
        def handle_write(reg_i=reg_i,
                         port=port,
                         i=port * nregs + reg_i,
                         j=(port - 1) * nregs + reg_i):
          if s.write_call[port] and s.write_addr[port] == reg_i:
            s.write_inc[i].v = s.write_data[port]
          elif port == 0:
            s.write_inc[i].v = s.regs[reg_i]
          else:
            s.write_inc[i].v = s.write_inc[j]

      # Compute the final state after all writes
      if num_write_ports == 0:

        @s.combinational
        def update_last(reg_i=reg_i):
          s.after_write[reg_i].v = s.regs[reg_i]
      else:

        @s.combinational
        def update_last(reg_i=reg_i, i=(num_write_ports - 1) * nregs + reg_i):
          s.after_write[reg_i].v = s.write_inc[i]

      # If writes are bypassed into dump, connect the dump output
      # to the result of the write, otherwise connect the dump
      # output to the current state
      if write_dump_bypass:
        s.connect(s.after_write[reg_i], s.dump_out[reg_i])
      else:
        s.connect(s.regs[reg_i], s.dump_out[reg_i])

      # Apply the set on top of all the writes
      @s.combinational
      def handle_set(reg_i=reg_i):
        if s.set_call:
          s.after_set[reg_i].v = s.set_in_[reg_i]
        else:
          s.after_set[reg_i].v = s.after_write[reg_i]

      # Tick the new values into each register
      @s.tick_rtl
      def update(reg_i=reg_i, value=reset_values[reg_i]):
        if s.reset:
          s.regs[reg_i].n = value
        else:
          s.regs[reg_i].n = s.after_set[reg_i]

    # Handle reads
    for port in range(num_read_ports):
      # If writes are bypassed into reads, use the new written values
      if write_read_bypass:

        @s.combinational
        def handle_read(port=port):
          s.read_data[port].v = s.after_set[s.read_addr[port]]
      else:

        @s.combinational
        def handle_read(port=port):
          s.read_data[port].v = s.regs[s.read_addr[port]]

  def line_trace(s):
    return ":".join(["{}".format(x) for x in s.regs])
