#=========================================================================
# CacheNetRTL_test.py
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

from lab5_mcore.CacheNetRTL import CacheNetRTL

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

    s.src      = [ TestSource      ( MemReqMsg(8, 32, 32), src_msg[i], src_delay  ) for i in xrange(4) ]
    s.cachenet =   CacheNetRTL     ()
    s.mem      =   TestMemory      ( MemMsg(8, 32, 32), 4, stall_prob, latency )
    s.sink     = [ TestNetCacheSink( MemRespMsg(8, 32), sink_msg[i], sink_delay ) for i in xrange(4) ]

    # Dump VCD

    if dump_vcd:
      s.cache.vcd_file = dump_vcd
      if hasattr(s.cache, 'inner'):
        s.cache.inner.vcd_file = dump_vcd

    # Connect

    for i in xrange( 4 ):
      s.connect( s.src[i].out,  s.cachenet.procreq[i]  )
      s.connect( s.sink[i].in_, s.cachenet.procresp[i] )

    for i in xrange( 4 ):
      s.connect( s.cachenet.cachereq[i],  s.mem.reqs[i]     )
      s.connect( s.cachenet.cacheresp[i], s.mem.resps[i]    )

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

    trace += s.cachenet.line_trace()

    for x in s.sink:
      trace += x.line_trace() + " "

    return trace

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  msg = MemReqMsg(8,32,32)

  if   type_ == 'rd': msg.type_ = MemReqMsg.TYPE_READ
  elif type_ == 'wr': msg.type_ = MemReqMsg.TYPE_WRITE
  elif type_ == 'in': msg.type_ = MemReqMsg.TYPE_WRITE_INIT

  msg.addr   = addr
  msg.opaque = opaque
  msg.len    = len
  msg.data   = data
  return msg

def resp( type_, opaque, test, len, data ):
  msg = MemRespMsg(8,32)

  if   type_ == 'rd': msg.type_ = MemRespMsg.TYPE_READ
  elif type_ == 'wr': msg.type_ = MemRespMsg.TYPE_WRITE
  elif type_ == 'in': msg.type_ = MemRespMsg.TYPE_WRITE_INIT

  msg.opaque = opaque
  msg.len    = len
  msg.test   = test
  msg.data   = data
  return msg

#----------------------------------------------------------------------
# Banked cache test
#----------------------------------------------------------------------
# We don't check hit/miss here, just use the messages.

def bank_test( base_addr ):
  return [
    # Bank 0
    #    type  opq  addr       len data                type  opq  test len data
    req( 'rd', 0x0, 0x00000000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x0eadbeef ),
    req( 'rd', 0x1, 0x00000100, 0, 0          ), resp( 'rd', 0x1, 0,   0,  0x00c0ffee ),
    req( 'rd', 0x2, 0x00000200, 0, 0          ), resp( 'rd', 0x2, 0,   0,  0x0fffffff ),
    req( 'rd', 0x3, 0x00000000, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0x0eadbeef ),
    # Bank 1
    #    type  opq  addr       len data                type  opq  test len data
    req( 'rd', 0x0, 0x00000010, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x1eadbeef ),
    req( 'rd', 0x1, 0x00000110, 0, 0          ), resp( 'rd', 0x1, 0,   0,  0x10c0ffee ),
    req( 'rd', 0x2, 0x00000210, 0, 0          ), resp( 'rd', 0x2, 0,   0,  0x1fffffff ),
    req( 'rd', 0x3, 0x00000010, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0x1eadbeef ),
    # Bank 2
    #    type  opq  addr       len data                type  opq  test len data
    req( 'rd', 0x0, 0x00000020, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x2eadbeef ),
    req( 'rd', 0x1, 0x00000120, 0, 0          ), resp( 'rd', 0x1, 0,   0,  0x20c0ffee ),
    req( 'rd', 0x2, 0x00000220, 0, 0          ), resp( 'rd', 0x2, 0,   0,  0x2fffffff ),
    req( 'rd', 0x3, 0x00000020, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0x2eadbeef ),
    # Bank 3
    #    type  opq  addr       len data                type  opq  test len data
    req( 'rd', 0x0, 0x00000030, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0x3eadbeef ),
    req( 'rd', 0x1, 0x00000130, 0, 0          ), resp( 'rd', 0x1, 0,   0,  0x30c0ffee ),
    req( 'rd', 0x2, 0x00000230, 0, 0          ), resp( 'rd', 0x2, 0,   0,  0x3fffffff ),
    req( 'rd', 0x3, 0x00000030, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0x3eadbeef ),
  ]

def bank_test_data( base_addr ):
  return [
    # addr      data (in int)
    0x00000000, 0x0eadbeef,
    0x00000100, 0x00c0ffee,
    0x00000200, 0x0fffffff,
    0x00000010, 0x1eadbeef,
    0x00000110, 0x10c0ffee,
    0x00000210, 0x1fffffff,
    0x00000020, 0x2eadbeef,
    0x00000120, 0x20c0ffee,
    0x00000220, 0x2fffffff,
    0x00000030, 0x3eadbeef,
    0x00000130, 0x30c0ffee,
    0x00000230, 0x3fffffff,
  ]

#----------------------------------------------------------------------
# Test Case: random
#----------------------------------------------------------------------

def random_msgs( base_addr ):

  vmem = [ random.randint(0,0xffffffff) for _ in range(20) ]
  msgs = []

  for i in range(20):
    msgs.extend([
      req( 'wr', i, base_addr+4*i, 0, vmem[i] ), resp( 'wr', i, 2, 0, 0 ),
    ])

  for i in range(20):
    idx = random.randint(0,19)

    if random.randint(0,1):

      correct_data = vmem[idx]
      msgs.extend([
        req( 'rd', i, base_addr+4*idx, 0, 0 ), resp( 'rd', i, 2, 0, correct_data ),
      ])

    else:

      new_data = random.randint(0,0xffffffff)
      vmem[idx] = new_data
      msgs.extend([
        req( 'wr', i, base_addr+4*idx, 0, new_data ), resp( 'wr', i, 2, 0, 0 ),
      ])

  return msgs

#-------------------------------------------------------------------------
# Test: Randomly read or write random data from random low addresses
#-------------------------------------------------------------------------
def rand_rw_lowaddr( base_addr, size, nways, nbanks, linesize, mem=None ):
  random.seed(0xbaadf00d)
  model = ModelCache(size, nways, nbanks, linesize, mem)
  for i in xrange(RAND_LEN):
    addr = random.randint(0x00000000, 0x00000400)
    addr = addr & Bits(32, 0xfffffffc) # Align the address
    if random.randint(0,1):
      # Write something
      value = random.getrandbits(32)
      model.write(addr, value)
    else:
      # Read something
      model.read(addr)
  return model.get_transactions()

# Fills 1K of memory randomly
def rand_mem( base_addr ):
  random.seed(0x00c0ffee)

  # This double list comprehension looks really icky, but my prior comments seem to suggest
  # that it was written this way for efficiency, whatever that meant at the time. The first
  # for is the outer loop, generating the addresses of 1K worth of memory. The second for
  # takes a tuple of (address, value), and turns it into two separate array elements, so that
  # it can be loaded into a test memory. ModelCache will undo the effects of the second for
  # when it reads the array in
  return [val for n in xrange(1024/4) for val in (n*4, random.randint(0x00000000, 0xffffffff))]


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
def test_cachenet( test_params, dump_vcd ):
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

