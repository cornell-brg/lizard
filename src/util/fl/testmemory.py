from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.cl import InValRdyRandStallAdapter
from pclib.cl import OutValRdyInelasticPipeAdapter
from util.line_block import LineBlock
from util.memory_model import MemoryModel
from msg.mem import MemMsgType


class TestMemoryFL( Model ):

  def __init__( s, mem_ifc_dtypes, nports=1, size=2**64 ):
    s.reqs = [ InValRdyBundle( mem_ifc_dtypes.req ) for _ in range( nports ) ]
    s.resps = [
        OutValRdyBundle( mem_ifc_dtypes.resp ) for _ in range( nports )
    ]
    assert mem_ifc_dtypes.req.data.nbits % 8 == 0
    assert mem_ifc_dtypes.resp.data.nbits % 8 == 0

    s.reqs_q = []
    for req in s.reqs:
      s.reqs_q.append( InValRdyRandStallAdapter( req, 0 ) )

    s.resps_q = []
    for resp in s.resps:
      s.resps_q.append( OutValRdyInelasticPipeAdapter( resp, 0 ) )

    s.mem = MemoryModel( mem_ifc_dtypes, size )

    @s.tick_cl
    def tick():
      for req_q, resp_q in zip( s.reqs_q, s.resps_q ):
        req_q.xtick()
        resp_q.xtick()
        if resp_q.full() or req_q.empty():
          continue
        memreq = req_q.deq()
        resp_q.enq( s.mem.handle_request( memreq ) )

  def line_trace( s ):
    return "TM"

  def write_mem( s, addr, data ):
    s.mem.write_mem( addr, data )

  def read_mem( s, addr, size ):
    s.mem.read_mem( addr, size )

  def cleanup( s ):
    s.mem.cleanup()
