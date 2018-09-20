#=========================================================================
# RouterRTL_test.py
#=========================================================================

from __future__    import print_function

import pytest
import random

from pymtl         import *
from pclib.test    import TestSource, TestNetSink, mk_test_case_table
from pclib.ifcs    import NetMsg

from lab4_net.RouterRTL import RouterRTL
from NetFL_test import mk_msg

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------
random.seed(0xdeadbeef)

class TestHarness( Model ):

  def __init__( s, RouterModel, router_id, src_msgs, sink_msgs, src_delay, sink_delay,
                num_ports, opaque_nbits, payload_nbits,
                dump_vcd=False, test_verilog=False ):

    s.src_msgs   = src_msgs
    s.sink_msgs  = sink_msgs
    s.src_delay  = src_delay
    s.sink_delay = sink_delay

    msg_type = NetMsg( num_ports, 2**opaque_nbits, payload_nbits )

    s.src    = [ TestSource  ( msg_type, s.src_msgs[x],  s.src_delay  )
                 for x in xrange( 3 ) ]

    s.router = RouterModel

    s.sink   = [ TestNetSink ( msg_type, s.sink_msgs[x], s.sink_delay )
                 for x in xrange( 3 ) ]

    # Dump VCD

    if dump_vcd:
      s.router.vcd_file = dump_vcd
      if hasattr(s.router, 'inner'):
        s.router.inner.vcd_file = dump_vcd


    # Translation

    if test_verilog:
      s.router = TranslationTool( s.router )

    # Connect

    s.connect( s.router.in0 , s.src[0].out  )
    s.connect( s.router.out0, s.sink[0].in_ )

    s.connect( s.router.in1 , s.src[1].out  )
    s.connect( s.router.out1, s.sink[1].in_ )

    s.connect( s.router.in2 , s.src[2].out  )
    s.connect( s.router.out2, s.sink[2].in_ )

    s.connect( s.router.router_id, router_id )

  def done( s ):
    done_flag = 1
    for i in xrange( 3 ):
      done_flag &= s.src[i].done and s.sink[i].done
    return done_flag

  def line_trace( s ):
    in_ = '|'.join( [ x.out.to_str( "%02s:%1s>%1s" % ( x.out.msg[32:40],
                                                       x.out.msg[40:42],
                                                       x.out.msg[42:44] ) )
                                        for x in s.src  ] )
    out = '|'.join( [ x.in_.to_str( "%02s:%1s>%1s" % ( x.in_.msg[32:40],
                                                       x.in_.msg[40:42],
                                                       x.in_.msg[42:44] ) )
                                        for x in s.sink ] )
    return in_ + ' > ' + s.router.line_trace() + ' > '+ out

#-------------------------------------------------------------------------
# run_router_test
#-------------------------------------------------------------------------

def run_router_test( RouterModel, router_id, src_delay, sink_delay, test_msgs,
                     dump_vcd = False, test_verilog = False,
                     num_ports = 4, opaque_nbits = 8, payload_nbits = 32 ):

  # src/sink msgs

  src_msgs  = test_msgs[0]
  sink_msgs = test_msgs[1]

  # Instantiate and elaborate the model

  model = TestHarness( RouterModel, router_id,
                       src_msgs, sink_msgs, src_delay, sink_delay,
                       num_ports, opaque_nbits, payload_nbits,
                       dump_vcd, test_verilog )

  model.vcd_file     = dump_vcd
  model.test_verilog = test_verilog
  model.elaborate()

  # Create a simulator using the simulation tool

  sim = SimulationTool( model )

  # Run the simulation

  print()

  sim.reset()
  while not model.done() and sim.ncycles < 1000:
    sim.print_line_trace()
    sim.cycle()

  # Add a couple extra ticks so that the VCD dump is nicer

  sim.cycle()
  sim.cycle()
  sim.cycle()

  # Check for success

  if not model.done():
    raise AssertionError( "Simulation did not complete!" )

def mk_router_msgs( nrouters, msg_list ):
  """Utility function to create the msgs from a list of msg parameters."""

  src_msgs  = [ [] for x in xrange(nrouters) ]
  sink_msgs = [ [] for x in xrange(nrouters) ]

  for x in msg_list:
    tsrc, tsink, src, dest, opaque, payload = x[0], x[1], x[2], x[3], x[4], x[5]

    msg = mk_msg( src, dest, opaque, payload, num_ports=nrouters )
    src_msgs [tsrc].append( msg )
    sink_msgs[tsink].append( msg )

  return [ src_msgs, sink_msgs ]

#-------------------------------------------------------------------------
# Test case: very basic messages
#-------------------------------------------------------------------------
# The testing approach for the router is basically the following.
# - tsrc: which _input port_ the router is getting a message from.
# - tsink: the _expected port_ the router should forward to.
# - src and dest are the _router ids_ for the _actual network_
#
# For example, say the router is number 2 (the parameter is at the bottom
# of this file), and we want to test if the router directly forward a
# message from inport #1 (input terminal) with src=dest=2 to output port
# #1 (output terminal).
# If your router fail to forward this message to the correct output port,
# the simulation will hang or fail, since the test sink connected
# to outport#1 expects to get a message but there is really no message
# for it, or some other test sink receives an unexpected message.

def very_basic_msgs( i ):

  nrouters = 4

  pre = i-1 if i>0        else nrouters-1
  nxt = i+1 if i<nrouters-1 else 0

  return mk_router_msgs( nrouters,
#       tsrc tsink src  dest opaque payload
    [ ( 0x1, 0x1,  i,   i,   0x00,  0xfe ), # deliver directly to #2
      ( 0x0, 0x2,  pre, nxt, 0x01,  0xde ), # pass it through
    ]
  )


def loopback_msgs(i):
  nrouters = 4
  pre = i-1 if i>0        else nrouters-1
  nxt = i+1 if i<nrouters-1 else 0
  even = i%2 == 0
  tsts = []

  for _ in range(100):
    lb = ( 0x1, 0x1,  i,   i,   random.randint(0, 0xff),  random.randint(0, 0xffffffff)) # deliver to itself
    tsts.append(lb)

  return mk_router_msgs( nrouters, tsts)


def adjacent_msgs( i ):
  nrouters = 4
  pre = i-1 if i>0        else nrouters-1
  nxt = i+1 if i<nrouters-1 else 0
  even = i%2 == 0
  tsts = []

  for _ in range(100):
    rgt = ( 0x1, 0x2,  i,   nxt,   random.randint(0, 0xff),  random.randint(0, 0xffffffff)) # deliver right
    lft = ( 0x1, 0x0,  i,   pre,   random.randint(0, 0xff),  random.randint(0, 0xffffffff)) # deliver left
    tsts.append(rgt)
    tsts.append(lft)

  return mk_router_msgs( nrouters, tsts)


def opp_msgs( i ):
  nrouters = 4
  pre = i-1 if i>0        else nrouters-1
  nxt = i+1 if i<nrouters-1 else 0
  opp = (i + 2)%nrouters
  even = i%2 == 0
  tsts = []

  for _ in range(100):
    if even:
        m = ( 0x1, 0x0,  i,   pre,   random.randint(0, 0xff),  random.randint(0, 0xffffffff)) # deliver left form 1
    else:
        m = ( 0x1, 0x2,  i,   nxt,   random.randint(0, 0xff),  random.randint(0, 0xffffffff)) # deliver right from 1
    tsts.append(m)

  return mk_router_msgs( nrouters, tsts)

#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# LAB TASK: Add new test cases
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#-------------------------------------------------------------------------
# Test Case Table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                       "msgs                routerid  src_delay sink_delay"),
  [ "vbasic_0",            very_basic_msgs(0), 0,        0,        0          ],
  [ "vbasic_1",            very_basic_msgs(1), 1,        0,        0          ],
  [ "vbasic_2",            very_basic_msgs(2), 2,        0,        0          ],
  [ "vbasic_3",            very_basic_msgs(3), 3,        0,        0          ],
  [ "adjacent_0",          adjacent_msgs(0),   0,        0,        0          ],
  [ "adjacent_1",          adjacent_msgs(1),   1,        0,        0          ],
  [ "adjacent_2",          adjacent_msgs(2),   2,        0,        0          ],
  [ "adjacent_3",          adjacent_msgs(3),   3,        0,        0          ],
  [ "adjacent_0_rd",       adjacent_msgs(0),   0,        1,        3          ],
  [ "adjacent_1_rd",       adjacent_msgs(1),   1,        4,        2          ],
  [ "adjacent_2_rd",       adjacent_msgs(2),   2,        5,        2          ],
  [ "adjacent_3_rd",       adjacent_msgs(3),   3,        2,        1          ],
  [ "loopback_0_nd",       loopback_msgs(0),   0,        0,        0          ],
  [ "loopback_1_nd",       loopback_msgs(1),   1,        0,        0          ],
  [ "loopback_2_nd",       loopback_msgs(2),   2,        0,        0          ],
  [ "loopback_3_nd",       loopback_msgs(3),   3,        0,        0          ],
  [ "loopback_0_rd",       loopback_msgs(0),   0,        2,        1          ],
  [ "loopback_1_rd",       loopback_msgs(1),   1,        0,        2          ],
  [ "loopback_2_rd",       loopback_msgs(2),   2,        4,        4          ],
  [ "loopback_3_rd",       loopback_msgs(3),   3,        1,        3          ],
  [ "opp_0_nd",            opp_msgs(0),        0,        0,        0          ],
  [ "opp_1_nd",            opp_msgs(1),        1,        0,        0          ],
  [ "opp_2_nd",            opp_msgs(2),        2,        0,        0          ],
  [ "opp_3_nd",            opp_msgs(3),        3,        0,        0          ],
  [ "opp_0_rd",            opp_msgs(0),        0,        2,        1          ],
  [ "opp_1_rd",            opp_msgs(1),        1,        3,        3          ],
  [ "opp_2_rd",            opp_msgs(2),        2,        4,        5          ],
  [ "opp_3_rd",            opp_msgs(3),        3,        1,        0          ],

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to leverage the additional lists
  # of request/response messages defined above, but also to test
  # different source/sink random delays.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])

#-------------------------------------------------------------------------
# Run tests
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table )
def test( test_params, dump_vcd, test_verilog ):
  run_router_test( RouterRTL(), test_params.routerid,
                   test_params.src_delay, test_params.sink_delay,
                   test_params.msgs, dump_vcd, test_verilog )
