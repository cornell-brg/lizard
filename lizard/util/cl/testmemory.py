from pymtl import *
from lizard.util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from lizard.util.line_block import LineBlock
from lizard.util.memory_model import MemoryModel
from lizard.msg.mem import MemMsgType


class TestMemoryCL(Model):

  def __init__(s, mem_ifc_dtypes, nports=1, size=2**64):
    s.reqs_q = [InValRdyCLPort(mem_ifc_dtypes.req) for _ in range(nports)]
    s.resps_q = [OutValRdyCLPort(mem_ifc_dtypes.resp) for _ in range(nports)]
    assert mem_ifc_dtypes.req.data.nbits % 8 == 0
    assert mem_ifc_dtypes.resp.data.nbits % 8 == 0

    s.mem = MemoryModel(mem_ifc_dtypes, size)

  def xtick(s):
    for req_q, resp_q in zip(s.reqs_q, s.resps_q):
      if resp_q.full() or req_q.empty():
        continue
      memreq = req_q.deq()
      resp_q.enq(s.mem.handle_request(memreq))

  def line_trace(s):
    return "TM"
    result = []
    for req, resp_q, resp in zip(s.reqs, s.resps_q, s.resps):
      result += ['> {}'.format(req), '< {}'.format(resp)]
      # trace_str += "{}({}){} ".format( req, resp_q, resp )

    return LineBlock(result)

  def write_mem(s, addr, data):
    s.mem.write_mem(addr, data)

  def read_mem(s, addr, size):
    s.mem.read_mem(addr, size)

  def cleanup(s):
    s.mem.cleanup()
