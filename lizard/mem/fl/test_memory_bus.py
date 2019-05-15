from functools import partial
from pymtl import *
from lizard.mem.rtl.memory_bus import MemMsgType
from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel


class TestMemoryBusFL(FLModel):

  # Implementations of the amo functions. First argument is the value read
  # from memory, the second argument is the data coming from the memory
  # request
  AMO_FUNS = {
      MemMsgType.AMO_ADD: lambda m, a: m + a,
      MemMsgType.AMO_AND: lambda m, a: m & a,
      MemMsgType.AMO_OR: lambda m, a: m | a,
      MemMsgType.AMO_XCHG: lambda m, a: a,
      MemMsgType.AMO_MIN: min,
      MemMsgType.AMO_MAX: max,
  }

  @HardwareModel.validate
  def __init__(s, memory_bus_interface, initial_memory=None, delays=None):
    super(TestMemoryBusFL, s).__init__(memory_bus_interface)
    if initial_memory is None:
      initial_memory = {}
    if delays is None:
      delays = [0] * memory_bus_interface.num_ports
    s.delays = delays
    s.data_nbytes = s.interface.data_nbytes
    s.data_nbits = s.data_nbytes * 8
    s.num_ports = memory_bus_interface.num_ports
    s.MemMsg = s.interface.MemMsg
    s.max_addr = s.MemMsg.req.addr._max

    s.state(
        results_delay=[-1 for _ in range(s.num_ports)],
        results=[None for _ in range(s.num_ports)],
    )
    s.mem = initial_memory

    for i in range(s.num_ports):
      recv_name = 'recv_{}'.format(i)
      send_name = 'send_{}'.format(i)
      cl_delay_name = 'cl_delay_{}'.format(i)
      s.model_method_explicit(cl_delay_name, partial(s.cl_delay, i), False)
      s.ready_method_explicit(recv_name, partial(s.recv_rdy, i), False)
      s.ready_method_explicit(send_name, partial(s.send_rdy, i), False)
      s.model_method_explicit(recv_name, partial(s.recv, i), False)
      s.model_method_explicit(send_name, partial(s.send, i), False)

  def recv_rdy(s, port):
    return s.results_delay[port] == 0

  def recv(s, port):
    s.results_delay[port] = -1
    return s.results[port]

  def cl_delay(s, port):
    if s.results_delay[port] != -1:
      if s.results_delay[port] != 0:
        s.results_delay[port] -= 1

  def send_rdy(s, port):
    return s.results_delay[port] == -1

  def send(s, port, msg):
    s.results_delay[port], s.results[port] = s.delays[port], s.handle_request(
        msg)

  def handle_request(s, req):
    nbytes = int(req.len_)
    if req.len_ == 0:
      nbytes = int(s.data_nbytes)
    addr = int(req.addr)

    if req.type_ == MemMsgType.READ:
      read_data = Bits(s.data_nbits)
      for j in range(nbytes):
        read_data[j * 8:j * 8 + 8] = s.mem.get(addr + j, 0)
      result = s.MemMsg.resp.mk_rd(req.opaque, req.len_, read_data)
    elif req.type_ == MemMsgType.WRITE:
      for j in range(nbytes):
        s.write_history[addr + j] = s.mem.get(addr + j, 0)
        s.mem[addr + j] = req.data[j * 8:j * 8 + 8].uint()
      result = s.MemMsg.resp.mk_wr(req.opaque, 0)
    elif req.type_ in TestMemoryBusFL.AMO_FUNS:
      read_data = Bits(s.data_nbits)
      for j in range(nbytes):
        read_data[j * 8:j * 8 + 8] = s.mem.get(addr + j, 0)
      write_data = s.AMO_FUNS[req.type_.uint()](read_data, req.data)
      for j in range(nbytes):
        s.write_history[addr + j] = s.mem.get(addr + j, 0)
        s.mem[addr + j] = write_data[j * 8:j * 8 + 8].uint()
      result = s.MemMsg.resp.mk_msg(req.type_, req.opaque, 0, req.len_,
                                    read_data)
    else:
      raise ValueError("Unknown memory message type: {}".format(req.type_))

    return result

  def write_mem(s, addr, data):
    assert addr + len(data) < s.max_addr
    for i, value in enumerate(data):
      s.mem[addr + i] = value & 0xff
      assert s.mem[int(addr + i)] == int(value & 0xff)

  def read_mem(s, addr, size):
    assert addr + size < s.max_addr
    result = Bits(size * 8)
    for i in range(size):
      result[i * 8:i * 8 + 8] = s.mem.get(addr + i)
    return result

  def _snapshot_model_state(s):
    s.write_history = {}

  def _restore_model_state(s, state):
    for addr, old_data in s.write_history.iteritems():
      s.mem[addr] = old_data
