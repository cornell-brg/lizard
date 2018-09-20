#=========================================================================
# IntMulFL_test
#=========================================================================

import pytest
import random

random.seed(0xdeadbeef)

from pymtl      import *
from pclib.test import mk_test_case_table, run_sim
from pclib.test import TestSource, TestSink

from lab1_imul.IntMulFL   import IntMulFL

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness (Model):

  def __init__( s, imul, src_msgs, sink_msgs,
                src_delay, sink_delay,
                dump_vcd=False, test_verilog=False ):

    # Instantiate models

    s.src  = TestSource ( Bits(64), src_msgs,  src_delay  )
    s.imul = imul
    s.sink = TestSink   ( Bits(32), sink_msgs, sink_delay )

    # Dump VCD

    if dump_vcd:
      s.imul.vcd_file = dump_vcd

    # Translation

    if test_verilog:
      s.imul = TranslationTool( s.imul )

    # Connect

    s.connect( s.src.out,  s.imul.req  )
    s.connect( s.imul.resp, s.sink.in_ )

  def done( s ):
    return s.src.done and s.sink.done

  def line_trace( s ):
    return s.src.line_trace()  + " > " + \
           s.imul.line_trace()  + " > " + \
           s.sink.line_trace()

#-------------------------------------------------------------------------
# mk_req_msg
#-------------------------------------------------------------------------

def req( a, b ):
  msg = Bits( 64 )
  msg[32:64] = Bits( 32, a, trunc=True )
  msg[ 0:32] = Bits( 32, b, trunc=True )
  return msg

def resp( a ):
  return Bits( 32, a, trunc=True )

#----------------------------------------------------------------------
# Test Case: small positive * positive
#----------------------------------------------------------------------

small_pos_pos_msgs = [
  req(  2,  3 ), resp(   6 ),
  req(  4,  5 ), resp(  20 ),
  req(  3,  4 ), resp(  12 ),
  req( 10, 13 ), resp( 130 ),
  req(  8,  7 ), resp(  56 ),
]

small_zero_msgs = [
  req(0, 1), resp(0),
  req(1, 0), resp(0),
  req(0,0), resp(0),
  req(100000,0), resp(0),
  req(0, 1000000), resp(0),
]

# ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define additional lists of request/response messages to create
# additional directed and random test cases.
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
small_neg_msgs = [item for sublist in ([ # First arg neg
  (req(x,y), resp(x*y)) for x in range(-5) for y in range(5)
] + [ # Second arg neg
  (req(x,y), resp(x*y)) for x in range(5) for y in range(-5)
] + [ #Both neg
  (req(x,y), resp(x*y)) for x in range(-5) for y in range(-5)
]) for item in sublist]


large_neg_msgs = [item for sublist in ([ # First arg neg
  (req(x,y), resp(x*y)) for x in range(-5, -2**31, -1234567890) for y in range(5, 2**31, 1234567890)
] + [ # Second arg neg
  (req(x,y), resp(x*y)) for x in range(5, 2**31, 1234567890) for y in range(-5, -2**31, -1234567890)
] + [ #Both neg
  (req(x,y), resp(x*y)) for x in range(-5, -2**31, -1234567890) for y in range(-5, -2**31, -1234567890)
]) for item in sublist]


large_pos_msgs = [item for sublist in ([ # First arg neg
  (req(x,y), resp(x*y)) for x in range(5, 2**31, 2345678901) for y in range(5, 2**31, 3456789012)
  ]) for item in sublist]



large_rand_msgs = [v for sl in ([(req(val[0],val[1]), resp(val[0]*val[1])) for val in
                                   [(random.randint(-2**31, 2**31), random.randint(-2**31,2**31)) for z in range(100)]])
                                  for v in sl]

edge_case_msgs = [
  req(0x80000000, 1), resp(0x80000000),
  req(0x80000000, 0x80000000), resp(0x80000000**2),
  req(0x01000001,0x00010000), resp(0x00010000*0x01000001),
  req(0x000F000F,0xF0F000F0), resp(0x000F000F*0xF0F000F0),
  req(0x80000000, 0x7FFFFFFF), resp(0x80000000*0x7FFFFFF),
]

#-------------------------------------------------------------------------
# Test Case Table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                      "msgs                 src_delay sink_delay"),
  [ "small_pos_pos",     small_pos_pos_msgs,   0,        0          ],

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to leverage the additional lists
  # of request/response messages defined above, but also to test
  # different source/sink random delays.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  ["small_zeros", small_zero_msgs, 0, 0],
  ["small_negs", small_neg_msgs, 0, 0],
  ["large_pos", large_pos_msgs, 0, 0],
  ["large_negs", large_neg_msgs, 0, 0],
  ["large_rand", large_rand_msgs, 0, 0],
  ["small_zeros", small_zero_msgs, 1, 2],
  ["small_negs", small_neg_msgs, 3, 4],
  ["large_negs", large_neg_msgs, 4, 3],
  ["large_rand", large_rand_msgs, 2, 1],
  ["edge_cases", edge_case_msgs, 6, 2],


])

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test( test_params, dump_vcd ):
  run_sim( TestHarness( IntMulFL(),
                        test_params.msgs[::2], test_params.msgs[1::2],
                        test_params.src_delay, test_params.sink_delay ),
           dump_vcd, max_cycles=20000 )
