from pymtl import *
from config.general import *
from msg.decode import *
from msg.packet_common import *


class WritebackPacket( BitStructDefinition ):

  def __init__( s ):
    CommonBundle( s )

    s.opcode = BitField( Opcode.bits )
    FieldValidPair( s, 'rd', REG_TAG_LEN )
    FieldValidPair( s, 'result', XLEN )
