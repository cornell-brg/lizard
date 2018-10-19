from pymtl import *
from config.general import *
from msg.mem import MemMsgStatus


class FetchPacket( BitStructDefinition ):

  def __init__( s ):
    s.stat = BitField( MemMsgStatus.bits )
    s.len = BitField( 1 )
    s.instr = BitField( ILEN )
    s.pc = BitField( XLEN )
    s.tag = BitField( INST_TAG_LEN )

  def __str__( s ):
    return "{}:{}:{}:{}".format( s.stat, s.len, s.instr, s.pc )
