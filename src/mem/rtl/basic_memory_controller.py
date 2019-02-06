from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from mem.rtl.memory_bus import MemMsgType, MemMsgStatus
from bitutil import clog2, clog2nz


class BasicMemoryControllerInterface(Interface):

  def __init__(s, memory_bus_interface, clients):
    s.mbi = memory_bus_interface
    methods = []
    for client in clients:
      methods.extend([
          MethodSpec(
              '{}_recv'.format(client),
              args=None,
              rets={
                  'type_': Bits(MemMsgType.bits),
                  'stat': Bits(MemMsgStatus.bits),
                  'len': Bits(clog2(s.mbi.data_nbytes)),
                  'data': Bits(s.sbi.data_nbytes * 8),
              },
              call=True,
              rdy=True,
          ),
          MethodSpec(
              '{}_send'.format(client),
              args={
                  'type_': Bits(MemMsgType.bits),
                  'addr': Bits(s.mbi.addr_nbits),
                  'len': Bits(clog2(s.mbi.data_nbytes)),
                  'data': Bits(s.mbi.data_nbytes * 8),
              },
              rets=None,
              call=True,
              rdy=True,
          ),
      ])

    super(BasicMemoryController, s).__init__(methods)


class BasicMemoryController(Model):

  def __init__(s, memory_bus_interface, clients):
    UseInterface(s, BasicMemoryControllerInterface(memory_bus_interface,
                                                   clients))

    if memory_bus_interface.num_ports != len(clients):
      raise ValueError('There should be exactly 1 port per client')
    if memory_bus_interface.opaque_nbits < clog2(len(clients)):
      raise ValueError('Not enough opaque bits')

    memory_bus_interface.require(
        s, 'bus', 'recv', count=memory_bus_interface.num_ports)
    memory_bus_interface.require(
        s, 'bus', 'send', count=memory_bus_interface.num_ports)

    nobits = clog2(memory_bus_interface.opaque_nbits)
    nclients = len(clients)
    s.recv_source_chains = [
        Wire(nobits) for _ in range(nclients * (nclients + 1))
    ]
    s.recv_valid_chains = [Wire(1) for _ in range(nclients * (nclients + 1))]

    s.index_client_recv_type_ = [Wire(MemMsgType.bits) for _ in range(nclients)]
    s.index_client_recv_stat = [
        Wire(MemMsgStatus.bits) for _ in range(nclients)
    ]
    s.index_client_recv_len = [
        Wire(clog2(memory_bus_interface.data_nbytes)) for _ in range(nclients)
    ]
    s.index_client_recv_addr = [
        Wire(memory_bus_interface.data_nbytes * 8) for _ in range(nclients)
    ]
    s.index_client_recv_rdy = [Wire(1) for _ in range(nclients)]
    s.index_client_recv_call = [Wire(1) for _ in range(nclients)]

    for i, client in enumerate(clients):
      client_send_port = getattr(s, '{}_send'.format(client))
      client_recv_port = getattr(s, '{}_recv'.format(client))

      s.connect(s.bus_send_type_[i], client_send_port.type_)
      s.connect(s.bus_send_addr[i], client_send_port.addr)
      s.connect(s.bus_send_len[i], client_send_port.len)
      s.connect(s.bus_send_data[i], client_send_port.data)
      s.connect(s.bus_send_opaque[i], i)
      s.connect(s.bus_send_call[i], client_send_port.call)
      s.connect(s.bus_send_rdy[i], client_send_port.rdy)

      s.connect(s.index_client_recv_type_[i], s.client_recv_port.type_)
      s.connect(s.index_client_recv_stat[i], s.client_recv_port.stat)
      s.connect(s.index_client_recv_len[i], s.client_recv_port.len)
      s.connect(s.index_client_recv_addr[i], s.client_recv_port.addr)
      s.connect(s.index_client_recv_rdy[i], s.client_recv_port.rdy)
      s.connect(s.index_client_recv_call[i], s.client_recv_port.call)

      base = i * (nclients + 1)
      s.connect(s.recv_source_chains[base], 0)
      s.connect(s.recv_valid_chains[base], 0)
      for j in range(nclients):

        @s.combinational
        def update_chains(i=i, j=j, last=base + j, curr=base + j + 1):
          if s.bus_recv_rdy[j] and s.bus_recv_opaque[j] == i:
            s.recv_source_chains[curr].v = j
            s.recv_valid_chains[curr].v = 1
          else:
            s.recv_source_chains[curr].v = s.recv_source_chains[last]
            s.recv_valid_chains[curr].v = s.recv_valid_chains[last]

      final = base + nclients

      @s.combinational
      def set_client_recv(i=i, final=final):
        s.index_client_recv_type_[i].v = s.bus_recv_type_[
            s.recv_source_chains[final]]
        s.index_client_recv_stat[i].v = s.bus_recv_stat[
            s.recv_source_chains[final]]
        s.index_client_recv_len[i].v = s.bus_recv_len[
            s.recv_source_chains[final]]
        s.index_client_recv_addr[i].v = s.bus_recv_addr[
            s.recv_source_chains[final]]
        s.index_client_recv_addr[i].v = s.recv_valid_chains[final]
        s.bus_recv_call[
            s.recv_source_chains[final]].v = s.index_client_recv_call[i]
