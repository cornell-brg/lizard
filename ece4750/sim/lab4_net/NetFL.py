#=========================================================================
# NetFL.py
#=========================================================================
# Function level model of on-chip network

from collections import deque

from pymtl       import *
from pclib.ifcs  import InValRdyBundle, OutValRdyBundle, NetMsg

class NetFL( Model ):

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( s, payload_nbits = 32 ):

    # Parameters

    num_ports = 4
    opaque_nbits = 8

    # Interface

    msg_type = NetMsg(num_ports, 2**opaque_nbits, payload_nbits)

    s.in_ = InValRdyBundle [num_ports]( msg_type )
    s.out = OutValRdyBundle[num_ports]( msg_type )

    s.output_fifos = [ deque() for x in xrange(num_ports) ]

    # Simulate the network
    @s.tick_cl
    def network_logic():

      # Dequeue logic
      for i, outport in enumerate( s.out ):
        if outport.val and outport.rdy:
          s.output_fifos[ i ].popleft()

      # Enqueue logic
      for i, inport in enumerate( s.in_ ):
        if inport.val and inport.rdy:
          s.output_fifos[ inport.msg.dest ].append( inport.msg[:] )

      # Set output signals
      for i, fifo in enumerate( s.output_fifos ):

        is_full  = len( fifo ) == 2**opaque_nbits
        is_empty = len( fifo ) == 0

        s.out[ i ].val.next = not is_empty
        s.in_[ i ].rdy.next = not is_full
        if not is_empty:
          s.out[ i ].msg.next = fifo[ 0 ]

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):

    traces = []
    for i in xrange( len(s.output_fifos) ):
      in_ = s.in_[ i ]
      out = s.out[ i ]
      in_str  = in_.to_str( "%02s:%1s>%1s" % ( in_.msg.opaque, in_.msg.src, in_.msg.dest ) )
      out_str = out.to_str( "%02s:%1s>%1s" % ( out.msg.opaque, out.msg.src, out.msg.dest ) )
      traces += [ '({}|{})'.format( in_str, out_str ) ]

    return ''.join( traces )
