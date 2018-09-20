#=========================================================================
# MsgAdapters.py
#=========================================================================
#                               +---------+
#                               |         |
#           +-----+             |         |             +-----+              
# memreq -->|     |-->netreq  ->|         |-> netreq -->|     |-->memreq
#           |  U  |             | network |             |  D  |              
# memresp<--|     |<--netresp <-|         |<- netresp<--|     |<--memresp
#           +-----+             |         |             +-----+              
#                               |         |
#                               +---------+

from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle, MemMsg, NetMsg

class UpstreamMsgAdapter( Model ):

#           +-----+          
# memreq -->|     |-->netreq 
#           |  U  |          
# memresp<--|     |<--netresp
#           +-----+

  def __init__( s, single_dest,
                   mopaque_nbits, addr_nbits, data_nbits,
                   nopaque_nbits, num_nodes ):

    # Parameters

    src_nbits   = clog2( num_nodes )

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    s.memifc     = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.netreqifc  = NetMsg( num_nodes, 2**nopaque_nbits, s.memifc.req.nbits  )
    s.netrespifc = NetMsg( num_nodes, 2**nopaque_nbits, s.memifc.resp.nbits )

    s.memreq     = InValRdyBundle ( s.memifc.req  )
    s.netreq     = OutValRdyBundle( s.netreqifc   )

    s.memresp    = OutValRdyBundle( s.memifc.resp )
    s.netresp    = InValRdyBundle ( s.netrespifc  )

    s.src_id     = InPort( src_nbits )

    #---------------------------------------------------------------------
    # Connections
    #---------------------------------------------------------------------

    s.connect( s.memreq.val, s.netreq.val )
    s.connect( s.memreq.rdy, s.netreq.rdy )

    s.connect( s.memresp.val, s.netresp.val )
    s.connect( s.memresp.rdy, s.netresp.rdy )

    # Modify memreq's opaque bit to add src information

    s.temp_memreq = Wire( s.memifc.req )
    s.connect( s.temp_memreq, s.netreq.msg.payload )

    @s.combinational
    def comb_req():
      if single_dest:
        s.netreq.msg.dest.value = 0
      else:
        s.netreq.msg.dest.value = s.memreq.msg.addr[4:6] # hard code 4 bank for now

      s.temp_memreq.value = s.memreq.msg
      s.temp_memreq.opaque[mopaque_nbits-src_nbits:mopaque_nbits].value = s.src_id

    s.connect( s.netreq.msg.src,    s.src_id )
    s.connect( s.netreq.msg.opaque, 0        )

    # Clear the opaque field of memresp

    @s.combinational
    def comb_resp():
      s.memresp.msg.value = s.netresp.msg.payload
      s.memresp.msg.opaque[mopaque_nbits-src_nbits:mopaque_nbits].value = 0

class DownstreamMsgAdapter( Model ):

#           +-----+              
# netreq -->|     |-->memreq
#           |  D  |              
# netresp<--|     |<--memresp
#           +-----+

  def __init__( s, single_dest,
                   mopaque_nbits, addr_nbits, data_nbits,
                   nopaque_nbits, num_nodes ):

    # Parameters

    src_nbits   = clog2( num_nodes )

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    s.memifc     = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.netreqifc  = NetMsg( num_nodes, 2**nopaque_nbits, s.memifc.req.nbits  )
    s.netrespifc = NetMsg( num_nodes, 2**nopaque_nbits, s.memifc.resp.nbits )

    s.netreq     = InValRdyBundle ( s.netreqifc  )
    s.netresp    = OutValRdyBundle( s.netrespifc )

    s.memreq     = OutValRdyBundle( s.memifc.req  )
    s.memresp    = InValRdyBundle ( s.memifc.resp )

    s.src_id     = InPort( src_nbits )

    #---------------------------------------------------------------------
    # Connections
    #---------------------------------------------------------------------

    s.connect( s.netreq.val, s.memreq.val )
    s.connect( s.netreq.rdy, s.memreq.rdy )

    s.connect( s.netresp.val, s.memresp.val )
    s.connect( s.netresp.rdy, s.memresp.rdy )

    # Just need to unpack netreq

    s.connect( s.netreq.msg.payload, s.memreq.msg )

    # For resp, need to pack memresp.msg with the header

    s.connect( s.netresp.msg.src,     s.src_id      )
    s.connect( s.netresp.msg.opaque,  0             )
    s.connect( s.netresp.msg.payload, s.memresp.msg )

    # Use the hidden dest information to determine the recipient

    @s.combinational
    def comb_resp():
      if single_dest:
        s.netresp.msg.dest.value = 0
      else:
        s.netresp.msg.dest.value = s.memresp.msg.opaque[mopaque_nbits-src_nbits:mopaque_nbits]
