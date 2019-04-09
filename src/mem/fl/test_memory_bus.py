from pymtl import *
from mem.rtl.memory_bus import MemMsgType, MemMsgStatus, MemoryBusInterface
from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from collections import deque
from functools import partial


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
  def __init__(s, memory_bus_interface, initial_memory={}):
    super(TestMemoryBusFL, s).__init__(memory_bus_interface)
    s.data_nbytes = s.interface.data_nbytes
    s.data_nbits = s.data_nbytes * 8
    s.num_ports = memory_bus_interface.num_ports
    s.MemMsg = s.interface.MemMsg
    s.max_addr = s.MemMsg.req.addr._max

    s.state(
        results=[deque() for _ in range(s.num_ports)],
        mem=initial_memory,
    )

    for i in range(s.num_ports):
      recv_name = 'recv_{}'.format(i)
      send_name = 'send_{}'.format(i)
      s.ready_method_explicit(recv_name, partial(s.recv_rdy, i), False)
      s.ready_method_explicit(send_name, partial(s.send_rdy, i), False)
      s.model_method_explicit(recv_name, partial(s.recv, i), False)
      s.model_method_explicit(send_name, partial(s.send, i), False)

  def recv_rdy(s, port):
    return len(s.results[port]) != 0

  def recv(s, port):
    return s.results[port].popleft()

  def send_rdy(s, port):
    return len(s.results[port]) == 0

  def send(s, port, msg):
    s.results[port].append(s.handle_request(msg))

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
        s.mem[addr + j] = req.data[j * 8:j * 8 + 8].uint()
      result = s.MemMsg.resp.mk_wr(req.opaque, 0)
    elif req.type_ in ASO_FUNS:
      read_data = Bits(s.data_nbits)
      for j in range(nbytes):
        read_data[j * 8:j * 8 + 8] = s.mem.get(addr + j, 0)
      write_data = s.AMO_FUNS[req.type_.uint()](read_data, req.data)
      for j in range(nbytes):
        s.mem[addr + j] = write_data[j * 8:j * 8 + 8].uint()
      result = s.MemMsg.resp.mk_msg(req.type_, req.opaque, 0, req.len_,
                                    read_data)
    else:
      raise ValueError("Unknown memory message type: {}".format(req.type_))

    return result

  def write_mem(s, addr, data):
    assert addr + len(data) < s.max_addr
    for i in range(len(data)):
      s.mem[addr + i] = data[i] & 0xff
      assert s.mem[int(addr + i)] == int(data[i] & 0xff)

  def read_mem(s, addr, size):
    assert addr + size < s.max_addr
    result = Bits(size * 8)
    for i in range(size):
      result[i * 8:i * 8 + 8] = s.mem.get(addr + i)
    return result
