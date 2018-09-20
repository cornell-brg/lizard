#=========================================================================
# FL model of Blocking Cache
#=========================================================================
# A function level cache model which only passes cache requests and
# responses to the memory.

from pymtl      import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.ifcs import MemMsg, MemReqMsg, MemRespMsg

class BlockingCacheFL( Model ):

  def __init__( s, num_banks=0, size=256,
                   opaque_nbits=8, addr_nbits=32,
                   data_nbits=32, cacheline_nbits=128 ):
    # Banking

    idx_shamt = clog2( num_banks ) if num_banks > 0 else 0

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # Proc <-> Cache

    s.cachereq  = InValRdyBundle ( MemReqMsg(opaque_nbits, addr_nbits, data_nbits)  )
    s.cacheresp = OutValRdyBundle( MemRespMsg(opaque_nbits, data_nbits) )

    # Cache <-> Mem

    s.memreq    = OutValRdyBundle( MemReqMsg(opaque_nbits, addr_nbits, cacheline_nbits)  )
    s.memresp   = InValRdyBundle ( MemRespMsg(opaque_nbits, cacheline_nbits) )

    #---------------------------------------------------------------------
    # Control
    #---------------------------------------------------------------------

    # pass through val/rdy signals

    s.connect( s.cachereq.val, s.memreq.val )
    s.connect( s.cachereq.rdy, s.memreq.rdy )

    s.connect( s.memresp.val, s.cacheresp.val )
    s.connect( s.memresp.rdy, s.cacheresp.rdy )

    #---------------------------------------------------------------------
    # Datapath
    #---------------------------------------------------------------------

    @s.combinational
    def logic():

      # Pass through requests: just copy all of the fields over, except
      # we zero extend the data field.

      if s.cachereq.msg.len == 0:
        len_ = 4
      else:
        len_ = s.cachereq.msg.len

      if s.cachereq.msg.type_ == MemReqMsg.TYPE_WRITE_INIT:
        s.memreq.msg.type_.value = MemReqMsg.TYPE_WRITE
      else:
        s.memreq.msg.type_.value = s.cachereq.msg.type_

      s.memreq.msg.opaque.value  = s.cachereq.msg.opaque
      s.memreq.msg.addr.value    = s.cachereq.msg.addr
      s.memreq.msg.len.value     = len_
      s.memreq.msg.data.value    = zext( s.cachereq.msg.data, 128 )

      # Pass through responses: just copy all of the fields over, except
      # we truncate the data field.

      len_ = s.memresp.msg.len
      if len_ == 4:
        len_ = 0

      s.cacheresp.msg.type_.value  = s.memresp.msg.type_
      s.cacheresp.msg.opaque.value = s.memresp.msg.opaque
      s.cacheresp.msg.test.value   = 0                        # "miss"
      s.cacheresp.msg.len.value    = len_
      s.cacheresp.msg.data.value   = s.memresp.msg.data[0:32]

  def line_trace(s):
    return "(forw)"
