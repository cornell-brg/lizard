from pymtl import *

import struct
from msg.mem import MemMsg8B
from pclib.test import TestSource, TestSink
from core.cl.proc import ProcCL
from util.cl.testmemory import TestMemoryCL
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort, cl_connect
from util.arch.rv64g import DATA_PACK_DIRECTIVE

from config.general import *
from util import line_block
from util.line_block import Divider


class ProcTestHarnessCL( Model ):

  def __init__( s ):

    s.src = TestSource( XLEN, [], 0 )
    s.sink = TestSink( XLEN, [], 0 )
    s.proc = ProcCL()
    s.mem = TestMemoryCL( MemMsg8B, 2 )

    @s.tick_cl
    def tick():
      s.proc.xtick()
      s.mem.xtick()

    s.connect( s.proc.mngr2proc, s.src.out )
    s.connect( s.proc.proc2mngr, s.sink.in_ )

    cl_connect( s.proc.imem_req, s.mem.reqs_q[ 0 ] )
    cl_connect( s.proc.imem_resp, s.mem.resps_q[ 0 ] )

    cl_connect( s.proc.dmem_req, s.mem.reqs_q[ 1 ] )
    cl_connect( s.proc.dmem_resp, s.mem.resps_q[ 1 ] )

  def load( self, mem_image ):
    sections = mem_image.get_sections()
    for section in sections:
      # For .mngr2proc sections, copy section into mngr2proc src
      if section.name == ".mngr2proc":
        for i in xrange( 0, len( section.data ), XLEN_BYTES ):
          bits = struct.unpack_from( DATA_PACK_DIRECTIVE,
                                     buffer( section.data, i,
                                             XLEN_BYTES ) )[ 0 ]
          self.src.src.msgs.append( Bits( XLEN, bits ) )
      # For .proc2mngr sections, copy section into proc2mngr_ref src
      elif section.name == ".proc2mngr":
        for i in xrange( 0, len( section.data ), XLEN_BYTES ):
          bits = struct.unpack_from( DATA_PACK_DIRECTIVE,
                                     buffer( section.data, i,
                                             XLEN_BYTES ) )[ 0 ]
          self.sink.sink.msgs.append( Bits( XLEN, bits ) )
      # For all other sections, simply copy them into the memory
      else:
        start_addr = section.addr
        temp = bytearray()
        temp.extend( section.data )
        for i in range( len( section.data ) ):
          self.mem.mem[ start_addr + i ] = temp[ i ]

  def cleanup( s ):
    s.mem.cleanup()

  def done( s ):
    return s.src.done and s.sink.done

  def line_trace( s ):
    return line_block.join([
        s.src.line_trace(),
        " > ",
        s.proc.line_trace(),
        Divider( " | " ),
        # s.mem.line_trace(),
        " > ",
        s.sink.line_trace()
    ] )
