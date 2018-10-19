from pymtl import *
from pclib.test import TestSource, TestSink
from util.freelist import FreeList


class Harness( Model ):

  def __init__( s ):
    s.sink = TestSink( FetchPacket(), sink_msgs, sink_delay )
    s.fetch_unit = FetchModel()
    s.mem = TestMemory( MemMsg4B, 1, mem_stall_prob, mem_latency )

    s.connect( s.fetch_unit.mem_req, s.mem.reqs[ 0 ] )
    s.connect( s.fetch_unit.mem_resp, s.mem.resps[ 0 ] )
    s.connect( s.fetch_unit.instrs, s.sink.in_ )

  def load_to_mem( self, addr, data ):
    for i in range( 0, data.nbits / 8 ):
      self.mem.mem[ addr + i ] = data[ i * 8:( i + 1 ) * 8 ].uint()

  def cleanup( s ):
    del s.mem.mem[: ]

  def done( s ):
    return s.sink.done

  def line_trace( s ):
    return s.fetch_unit.line_trace() + " > " + s.mem.line_trace()
