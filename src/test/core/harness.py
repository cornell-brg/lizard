#=========================================================================
# test_harness
#=========================================================================
# Includes a test harness that composes a processor, src/sink, and test
# memory, and a run_test function.

import struct
import inspect

from pymtl import *

from msg import MemMsg4B
from pclib.test import TestSource, TestSink
from pclib.test import TestMemory

from util.tinyrv2_encoding import assemble, DATA_PACK_DIRECTIVE

from config.general import *

#=========================================================================
# TestHarness
#=========================================================================
# Use this with pytest parameterize so that the name of the function that
# generates the assembly test ends up as part of the actual test case
# name. Here is an example:
#
#  @pytest.mark.parametrize( "name,gen_test", [
#    asm_test( gen_basic_test  ),
#    asm_test( gen_bypass_test ),
#    asm_test( gen_value_test  ),
#  ])
#  def test( name, gen_test ):
#    run_test( ProcFL, gen_test )
#


def asm_test( func ):
  name = func.__name__
  if name.startswith( "gen_" ):
    name = name[ 4:]
  if name.endswith( "_test" ):
    name = name[:-5 ]
  return ( name, func )


def is_mod_function( mod, func ):
  return inspect.isfunction( func ) and inspect.getmodule( func ) == mod


def list_functions( mod ):
  return [
      func for func in mod.__dict__.itervalues()
      if is_mod_function( mod, func )
  ]


def clean_module_name( m, n=2 ):
  return '-'.join( m.__name__.split( '.' )[-n:] )


def extract_module_tests( m ):
  funcs = [ f for f in list_functions( m ) if f.__name__.endswith( '_test' ) ]
  result = [( '{}_{}'.format( clean_module_name( m ), name ), func )
            for name, func in [ asm_test( f ) for f in funcs ] ]
  return result


def extract_tests( ms ):
  return [ test_pair for m in ms for test_pair in extract_module_tests( m ) ]


#=========================================================================
# TestHarness
#=========================================================================


class TestHarness( Model ):

  #-----------------------------------------------------------------------
  # constructor
  #-----------------------------------------------------------------------

  def __init__( s, ProcModel, dump_vcd, src_delay, sink_delay, mem_stall_prob,
                mem_latency ):

    s.src = TestSource( XLEN, [], src_delay )
    s.sink = TestSink( XLEN, [], sink_delay )
    s.proc = ProcModel()
    s.mem = TestMemory( MemMsg4B, 1, mem_stall_prob, mem_latency )

    # Dump VCD

    if dump_vcd:
      s.proc.vcd_file = dump_vcd

    # Processor <-> Proc/Mngr

    s.connect( s.proc.mngr2proc, s.src.out )
    s.connect( s.proc.proc2mngr, s.sink.in_ )

    # Processor <-> Memory

    s.connect( s.proc.mem_req, s.mem.reqs[ 0 ] )
    s.connect( s.proc.mem_resp, s.mem.resps[ 0 ] )

  #-----------------------------------------------------------------------
  # load
  #-----------------------------------------------------------------------

  def load( self, mem_image ):

    # Iterate over the sections

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
        stop_addr = section.addr + len( section.data )
        self.mem.mem[ start_addr:stop_addr ] = section.data

  #-----------------------------------------------------------------------
  # cleanup
  #-----------------------------------------------------------------------

  def cleanup( s ):
    del s.mem.mem[: ]

  #-----------------------------------------------------------------------
  # done
  #-----------------------------------------------------------------------

  def done( s ):
    return s.src.done and s.sink.done

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return s.src.line_trace()  + " >" + \
           ("- " if s.proc.stats_en else "  ") + \
           s.proc.line_trace() + "|" + \
           s.mem.line_trace()  + " > " + \
           s.sink.line_trace()


#=========================================================================
# run_test
#=========================================================================


def run_test( ProcModel,
              gen_test,
              dump_vcd=None,
              src_delay=0,
              sink_delay=0,
              mem_stall_prob=0,
              mem_latency=0,
              max_cycles=20000,
              extra_cycles=3 ):

  # Instantiate and elaborate the model

  model = TestHarness( ProcModel, dump_vcd, src_delay, sink_delay,
                       mem_stall_prob, mem_latency )

  model.vcd_file = dump_vcd
  model.elaborate()

  # Assemble the test program
  asm = gen_test()
  # We CANNOT just walk of the end because of extra cycles
  # That will trigger an illegal instruction exception
  trailer = '\n'.join([ 'nop' ] * extra_cycles )
  if isinstance( asm, list ):
    for seq in asm:
      print( seq )
    asm += [ trailer ]
  else:
    print( asm )
    asm += trailer
  mem_image = assemble( asm )

  # Load the program into the model

  model.load( mem_image )

  # Create a simulator using the simulation tool

  sim = SimulationTool( model )

  # Run the simulation

  print()

  sim.reset()
  while not model.done() and sim.ncycles < max_cycles:
    sim.print_line_trace()
    sim.cycle()

  # print the very last line trace after the last tick

  sim.print_line_trace()

  # Force a test failure if we timed out

  assert sim.ncycles < max_cycles

  # Add a couple extra ticks so that the VCD dump is nicer
  for _ in range( extra_cycles ):
    sim.cycle()

  model.cleanup()
