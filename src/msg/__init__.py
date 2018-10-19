import msg.mem
import config.general
import config.mem


class MemMsg( object ):

  def __init__( s, opaque_nbits, addr_nbits, data_nbits ):
    s.req = msg.mem.MemReqMsg( opaque_nbits, addr_nbits, data_nbits )
    s.resp = msg.mem.MemRespMsg( opaque_nbits, data_nbits )


MemMsg4B = MemMsg( config.mem.OPAQUE_SIZE, config.general.XLEN, 32 )
MemMsg8B = MemMsg( config.mem.OPAQUE_SIZE, config.general.XLEN, 64 )
MemMsg16B = MemMsg( config.mem.OPAQUE_SIZE, config.general.XLEN, 128 )
