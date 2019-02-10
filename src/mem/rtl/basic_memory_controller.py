from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from mem.rtl.memory_bus import MemMsgType, MemMsgStatus
from util.rtl.mux import Mux
from util.rtl.register import Register
from bitutil import clog2, clog2nz


class BasicMemoryControllerInterface(Interface):

  def __init__(s, mem_msg, clients):
    s.MemMsg = mem_msg
    methods = []
    for client in clients:
      methods.extend([
          MethodSpec(
              '{}_recv'.format(client),
              args=None,
              rets={'resp': mem_msg.resp},
              call=True,
              rdy=True,
          ),
          MethodSpec(
              '{}_send'.format(client),
              args={'req': mem_msg.req},
              rets=None,
              call=True,
              rdy=True,
          ),
      ])

    super(BasicMemoryControllerInterface, s).__init__(methods)


class BasicMemoryController(Model):

  def __init__(s, memory_bus_interface, clients):
    UseInterface(
        s, BasicMemoryControllerInterface(memory_bus_interface.MemMsg, clients))

    if memory_bus_interface.num_ports != len(clients):
      raise ValueError('There should be exactly 1 port per client')
    if memory_bus_interface.opaque_nbits < clog2(len(clients)):
      raise ValueError('Not enough opaque bits')

    memory_bus_interface.require(
        s, 'bus', 'recv', count=memory_bus_interface.num_ports)
    memory_bus_interface.require(
        s, 'bus', 'send', count=memory_bus_interface.num_ports)

    nobits = memory_bus_interface.opaque_nbits
    nclients = len(clients)
    s.in_flight = Wire(nclients)
    s.can_send = Wire(nclients)
    s.in_flight_next = Wire(nclients)

    s.client_send_rdy = [Wire(1) for _ in range(nclients)]
    s.index_client_recv_call = [Wire(1) for _ in range(nclients)]
    s.index_client_recv_rdy = [Wire(1) for _ in range(nclients)]
    s.recv_source_chains = [
        Wire(nobits) for _ in range(nclients * (nclients + 1))
    ]
    s.recv_valid_chains = [Wire(1) for _ in range(nclients * (nclients + 1))]

    s.client_muxes = [
        Mux(memory_bus_interface.MemMsg.resp, nclients) for _ in range(nclients)
    ]
    s.client_regs = [
        Register(memory_bus_interface.MemMsg.resp, True)
        for _ in range(nclients)
    ]
    s.client_valid_regs = [Register(1, True) for _ in range(nclients)]

    # PYMTL_BROKEN
    s.bus_recv_msg_opaque = [Wire(nobits) for _ in range(nclients)]

    for i, client in enumerate(clients):
      client_send_port = getattr(s, '{}_send'.format(client))
      client_recv_port = getattr(s, '{}_recv'.format(client))
      s.connect(s.index_client_recv_call[i], client_recv_port.call)
      s.connect(s.index_client_recv_rdy[i], client_recv_port.rdy)

      s.connect(s.bus_send_msg[i].type_, client_send_port.req.type_)
      s.connect(s.bus_send_msg[i].addr, client_send_port.req.addr)
      s.connect(s.bus_send_msg[i].len_, client_send_port.req.len_)
      s.connect(s.bus_send_msg[i].data, client_send_port.req.data)
      s.connect(s.bus_send_msg[i].opaque, i)
      s.connect(s.bus_send_call[i], client_send_port.call)

      @s.combinational
      def compute_client_send_rdy(i=i):
        s.client_send_rdy[i].v = s.bus_send_rdy[i] and s.can_send[i]

      s.connect(s.client_send_rdy[i], client_send_port.rdy)

      base = i * (nclients + 1)
      s.connect(s.recv_source_chains[base], 0)
      s.connect(s.recv_valid_chains[base], 0)
      s.connect(s.bus_recv_msg_opaque[i], s.bus_recv_msg[i].opaque)

      for j in range(nclients):

        @s.combinational
        def update_chains(i=i, j=j, last=base + j, curr=base + j + 1):
          if s.bus_recv_rdy[j] and s.bus_recv_msg_opaque[j] == i:
            s.recv_source_chains[curr].v = j
            s.recv_valid_chains[curr].v = 1
          else:
            s.recv_source_chains[curr].v = s.recv_source_chains[last]
            s.recv_valid_chains[curr].v = s.recv_valid_chains[last]

        s.connect(s.client_muxes[i].mux_in_[j], s.bus_recv_msg[j])

      final = base + nclients

      s.connect(s.client_muxes[i].mux_select, s.recv_source_chains[final])
      s.connect(s.client_regs[i].write_data, s.client_muxes[i].mux_out)
      s.connect(s.client_regs[i].write_call, s.recv_valid_chains[final])

      @s.combinational
      def update_valid_data_and_rdy(i=i, final=final):
        s.client_valid_regs[i].write_data.v = s.recv_valid_chains[
            final] and not s.index_client_recv_call[i]
        s.index_client_recv_rdy[i].v = s.recv_valid_chains[
            final] or s.client_valid_regs[i].read_data

      s.connect(s.client_valid_regs[i].write_call, s.recv_valid_chains[final])

      s.connect(client_recv_port.resp.type_, s.client_regs[i].read_data.type_)
      s.connect(client_recv_port.resp.stat, s.client_regs[i].read_data.stat)
      s.connect(client_recv_port.resp.len_, s.client_regs[i].read_data.len_)
      s.connect(client_recv_port.resp.data, s.client_regs[i].read_data.data)

      # always read from the bus into the register if ready
      s.connect(s.bus_recv_call[i], s.bus_recv_rdy[i])

      @s.combinational
      def compute_can_send(i=i):
        if s.in_flight[i]:
          s.can_send[i].v = s.index_client_recv_call[i]
        else:
          s.can_send[i].v = 1

      @s.combinational
      def compute_in_flight_next(i=i):
        if s.bus_send_call[i]:
          s.in_flight_next[i] = 1
        elif s.index_client_recv_call[i]:
          s.in_flight_next[i] = 0
        else:
          s.in_flight_next[i] = s.in_flight[i]

    @s.tick_rtl
    def update_in_flight():
      if s.reset:
        s.in_flight.n = 0
      else:
        s.in_flight.n = s.in_flight_next
