from pymtl import *
from lizard.msg.mem import MemMsgType


class MemoryModel(object):

  def __init__(s, dtype, size):
    s.mem = {}
    s.dtype = dtype
    s.mk_rd_resp = dtype.resp.mk_rd
    s.mk_wr_resp = dtype.resp.mk_wr
    s.mk_misc_resp = dtype.resp.mk_msg
    s.data_nbits = dtype.req.data.nbits
    s.size = size

  def handle_request(s, memreq):
    # When len is zero, then we use all of the data
    nbytes = memreq.len
    if memreq.len == 0:
      nbytes = s.data_nbits / 8

    assert memreq.addr + nbytes <= s.size

    if memreq.type_ == MemMsgType.READ:
      read_data = Bits(s.data_nbits)
      for j in range(nbytes):
        read_data[j * 8:j * 8 + 8] = s.mem.get(int(memreq.addr + j), 0)
      result = s.mk_rd_resp(memreq.opaque, memreq.len, read_data)
    elif memreq.type_ == MemMsgType.WRITE:
      for j in range(nbytes):
        s.mem[int(memreq.addr + j)] = memreq.data[j * 8:j * 8 + 8].uint()
      result = s.mk_wr_resp(memreq.opaque, 0)
    elif memreq.type_ in MemoryModel.AMO_FUNS:
      read_data = Bits(s.data_nbits)
      for j in range(nbytes):
        read_data[j * 8:j * 8 + 8] = s.mem.get(int(memreq.addr + j), 0)

      write_data = AMO_FUNS[memreq.type_.uint()](read_data, memreq.data)

      for j in range(nbytes):
        s.mem[int(memreq.addr + j)] = write_data[j * 8:j * 8 + 8].uint()
      result = s.mk_misc_resp(memreq.type_, memreq.opaque, memreq.len,
                              read_data)
    else:
      raise ValueError("Unknown memory message type: {}".format(memreq.type_))

    return result

  def write_mem(s, addr, data):
    assert addr + len(data) < s.size
    for i in range(len(data)):
      s.mem[addr + i] = data[i]

  def read_mem(s, addr, size):
    assert addr + size < s.size
    result = bytearray()
    for i in range(size):
      result.append(s.mem.get(addr + i), 0)
    return result

  def cleanup(s):
    s.mem.clear()


#-------------------------------------------------------------------------
# AMO_FUNS
#-------------------------------------------------------------------------
# Implementations of the amo functions. First argument is the value read
# from memory, the second argument is the data coming from the memory
# request.

AMO_FUNS = {
    MemMsgType.AMO_ADD: lambda m, a: m + a,
    MemMsgType.AMO_AND: lambda m, a: m & a,
    MemMsgType.AMO_OR: lambda m, a: m | a,
    MemMsgType.AMO_XCHG: lambda m, a: a,
    MemMsgType.AMO_MIN: min,
    MemMsgType.AMO_MAX: max,
}
