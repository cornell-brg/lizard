from pymtl import *
from config.general import *
from msg.decode import *
from msg.packet_common import *


class ExecutePacket( BitStructDefinition ):

  def __init__( s ):
    CommonBundle( s )

    s.opcode = BitField( Opcode.bits )
    FieldValidPair( s, 'rd', REG_TAG_LEN )
    FieldValidPair( s, 'result', XLEN )

  def __str__( s ):
    return 'inst:{: <5} rd:{} v:{} result: {}'.format(
        RV64Inst.name( s.inst ), s.rd, s.rd_valid, s.result )
