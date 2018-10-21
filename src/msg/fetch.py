from pymtl import *
from config.general import *
from msg.mem import MemMsgStatus


class FetchPacket( BitStructDefinition ):

  def __init__( s ):
    s.instr = BitField( ILEN )
    s.pc = BitField( XLEN )
    s.tag = BitField( INST_TAG_LEN )

  def __str__( s ):
    return "{}:{}:{}".format( s.instr, s.pc, s.tag )
