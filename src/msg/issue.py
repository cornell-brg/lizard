from pymtl import *
from msg.decode import *
from config.general import *
from msg.packet_common import *


class IssuePacket( BitStructDefinition ):

  def __init__( s ):
    CommonBundle( s )
    DecodeBundle( s )

    FieldValidPair( s, 'rs1', XLEN )
    FieldValidPair( s, 'rs2', XLEN )
    FieldValidPair( s, 'rd', REG_TAG_LEN )

    ExceptionBundle( s )

  def __str__( s ):
    return 'imm:{} inst:{: <5} rs1:{} v:{} rs2:{} v:{} rd:{} v:{}'.format(
        s.imm, RV64Inst.name( s.inst ), s.rs1, s.rs1_valid, s.rs2, s.rs2_valid,
        s.rd, s.rd_valid )
