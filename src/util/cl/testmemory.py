#=========================================================================
# TestMemoryCL
#=========================================================================
# A behavioral Test Memory which is parameterized based on the number of
# memory request/response ports. This version is a little different from
# the one in pclib because we actually use the memory messages correctly
# in the interface.

from pymtl import *
from pclib.ifcs import MemMsg, MemReqMsg, MemRespMsg, MemMsg4B
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from util.line_block import LineBlock
from msg.mem import MemMsgType

import binascii

#-------------------------------------------------------------------------
# TestMemoryCL
#-------------------------------------------------------------------------


class TestMemoryCL( Model ):

  def __init__( s, mem_ifc_dtypes=MemMsg4B(), nports=1, mem_nbytes=2**20 ):

    # Interface

    xr = range
    s.reqs_q = [ InValRdyCLPort( mem_ifc_dtypes.req ) for _ in xr( nports ) ]
    s.resps_q = [ OutValRdyCLPort( mem_ifc_dtypes.resp ) for _ in xr( nports ) ]

    # Checks

    assert mem_ifc_dtypes.req.data.nbits % 8 == 0
    assert mem_ifc_dtypes.resp.data.nbits % 8 == 0

    s.mem = bytearray( mem_nbytes )

    s.mk_rd_resp = mem_ifc_dtypes.resp.mk_rd
    s.mk_wr_resp = mem_ifc_dtypes.resp.mk_wr
    s.mk_misc_resp = mem_ifc_dtypes.resp.mk_msg
    s.data_nbits = mem_ifc_dtypes.req.data.nbits
    s.nports = nports

  #---------------------------------------------------------------------
  # Tick
  #---------------------------------------------------------------------
  def xtick( s ):
    for req_q, resp_q in zip( s.reqs_q, s.resps_q ):
      if resp_q.full():
        continue

      if not req_q.empty():
        memreq = req_q.deq()

        # When len is zero, then we use all of the data
        nbytes = memreq.len
        if memreq.len == 0:
          nbytes = s.data_nbits / 8

        if memreq.type_ == MemReqMsg.TYPE_READ:
          # Copy the bytes from the bytearray into read data bits
          read_data = Bits( s.data_nbits )
          for j in range( nbytes ):
            read_data[ j * 8:j * 8 + 8 ] = s.mem[ memreq.addr + j ]

          resp_q.enq( s.mk_rd_resp( memreq.opaque, memreq.len, read_data ) )
        elif memreq.type_ == MemReqMsg.TYPE_WRITE:
          # Copy write data bits into bytearray
          write_data = memreq.data
          for j in range( nbytes ):
            s.mem[ memreq.addr + j ] = write_data[ j * 8:j * 8 + 8 ].uint()

          resp_q.enq( s.mk_wr_resp( memreq.opaque, 0 ) )
        elif ( memreq.type_ == MemReqMsg.TYPE_AMO_ADD or
               memreq.type_ == MemReqMsg.TYPE_AMO_AND or
               memreq.type_ == MemReqMsg.TYPE_AMO_OR or
               memreq.type_ == MemReqMsg.TYPE_AMO_XCHG or
               memreq.type_ == MemReqMsg.TYPE_AMO_MIN ):
          req_data = memreq.data

          # Copy the bytes from the bytearray into read data bits
          read_data = Bits( s.data_nbits )
          for j in range( nbytes ):
            read_data[ j * 8:j * 8 + 8 ] = s.mem[ memreq.addr + j ]

          write_data = AMO_FUNS[ memreq.type_.uint() ]( read_data, req_data )

          # Copy write data bits into bytearray
          for j in range( nbytes ):
            s.mem[ memreq.addr + j ] = write_data[ j * 8:j * 8 + 8 ].uint()

          resp_q.enq(
              s.mk_misc_resp( memreq.type_, memreq.opaque, memreq.len,
                              read_data ) )
        # Unknown message type -- throw an exception
        else:
          raise Exception(
              "TestMemoryCL doesn't know how to handle message type {}".format(
                  memreq.type_ ) )

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return "TM"
    result = []
    for req, resp_q, resp in zip( s.reqs, s.resps_q, s.resps ):
      result += [ '> {}'.format( req ), '< {}'.format( resp ) ]
      # trace_str += "{}({}){} ".format( req, resp_q, resp )

    return LineBlock( result )

  #-----------------------------------------------------------------------
  # write_mem
  #-----------------------------------------------------------------------
  # Writes the list of bytes to the given memory address.

  def write_mem( s, addr, data ):
    assert len( s.mem ) > ( addr + len( data ) )
    s.mem[ addr:addr + len( data ) ] = data

  #-----------------------------------------------------------------------
  # read_mem
  #-----------------------------------------------------------------------
  # Reads size bytes from the given memory address.

  def read_mem( s, addr, size ):
    assert len( s.mem ) > ( addr + size )
    return s.mem[ addr:addr + size ]

  def cleanup( s ):
    del s.mem[: ]


#-------------------------------------------------------------------------
# AMO_FUNS
#-------------------------------------------------------------------------
# Implementations of the amo functions. First argument is the value read
# from memory, the second argument is the data coming from the memory
# request.

AMO_FUNS = {
    MemReqMsg.TYPE_AMO_ADD: lambda m, a: m + a,
    MemReqMsg.TYPE_AMO_AND: lambda m, a: m & a,
    MemReqMsg.TYPE_AMO_OR: lambda m, a: m | a,
    MemReqMsg.TYPE_AMO_XCHG: lambda m, a: a,
    MemReqMsg.TYPE_AMO_MIN: min,
}
