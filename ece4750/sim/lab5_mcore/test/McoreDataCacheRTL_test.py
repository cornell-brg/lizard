#=========================================================================
# McoreDataCacheRTL_test.py
#=========================================================================

from __future__ import print_function

import pytest
import random
import struct

from pymtl      import *
from pclib.test import mk_test_case_table, run_sim
from pclib.test import TestSource
from pclib.test import TestMemory

from pclib.ifcs import MemMsg,    MemReqMsg,    MemRespMsg

from TestNetCacheSink   import TestNetCacheSink

from lab5_mcore.McoreDataCacheRTL import McoreDataCacheRTL

class TestHarness( Model ):

  def __init__( s, src_msgs, sink_msgs, stall_prob, latency,
                src_delay, sink_delay, dump_vcd ):

  # Here we assume 16B cacheline, so the bank bits are slice(4, 6)
  # +--------------------------+--------------+--------+--------+--------+
  # |        22b               |     4b       |   2b   |   2b   |   2b   |
  # |        tag               |   index      |bank idx| offset | subwd  |
  # +--------------------------+--------------+--------+--------+--------+

    src_msg = [ [], [], [], [] ]
    sink_msg = [ [], [], [], [] ]

    for i in xrange( len(src_msgs) ):
      src_msg[src_msgs[i].addr[5:7].uint()].append(src_msgs[i])
      sink_msg[src_msgs[i].addr[5:7].uint()].append(sink_msgs[i])

    # Instantiate models

    s.src   = [ TestSource       ( MemReqMsg(8, 32, 32), src_msg[i], src_delay  ) for i in xrange(4) ]
    s.cache =   McoreDataCacheRTL()
    s.mem   =   TestMemory       ( MemMsg(8, 32, 128), 1, stall_prob, latency )
    s.sink  = [ TestNetCacheSink ( MemRespMsg(8, 32), sink_msg[i], sink_delay ) for i in xrange(4) ]

    # Dump VCD

    if dump_vcd:
      s.cache.vcd_file = dump_vcd
      if hasattr(s.cache, 'inner'):
        s.cache.inner.vcd_file = dump_vcd

    # Connect

    for i in xrange( 4 ):
      s.connect( s.src[i].out,  s.cache.procreq[i]  )
      s.connect( s.sink[i].in_, s.cache.procresp[i] )

    s.connect( s.cache.mainmemreq,  s.mem.reqs[0]     )
    s.connect( s.cache.mainmemresp, s.mem.resps[0]    )

  def load( s, addrs, data_ints ):
    for addr, data_int in zip( addrs, data_ints ):
      data_bytes_a = bytearray()
      data_bytes_a.extend( struct.pack("<I",data_int) )
      s.mem.write_mem( addr, data_bytes_a )

  def done( s ):
    return all([x.done for x in s.src]) and all([x.done for x in s.sink])

  def line_trace( s ):
    trace = ""
    for x in s.src:
      trace += x.line_trace() + " "

    trace += s.cache.line_trace()

    for x in s.sink:
      trace += x.line_trace() + " "

    return trace

from CacheNetRTL_test import bank_test, bank_test_data
from CacheNetRTL_test import random_msgs

#-------------------------------------------------------------------------
# Test table
#-------------------------------------------------------------------------

test_case_table = mk_test_case_table([
  (                    "msg_func     mem_data_func   stall lat src sink"),
  [ "bank_test",        bank_test,   bank_test_data, 0.0,  0,  0,  0    ],
  [ "bank_test_stall",  bank_test,   bank_test_data, 0.5,  4,  3,  14   ],
  [ "random",           random_msgs, None,           0.0,  0,  0,  0    ],
  [ "random_stall",     random_msgs, None,           0.5,  4,  3,  14   ],
])


@pytest.mark.parametrize( **test_case_table )
def test_dcache( test_params, dump_vcd ):
  msgs = test_params.msg_func( 0 )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( 0 )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         dump_vcd )
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, dump_vcd )

