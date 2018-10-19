from pymtl import *
from config.general import *
from msg.decode import *


class ResultPacket( BitStructDefinition ):

  def __init__( s ):
    s.inst = BitField( RV64Inst.bits )
    s.rd = BitField( REG_TAG_LEN )
    s.rd_valid = BitField( 1 )
    s.result = BitField( XLEN )

    s.csr = BitField( CSR_SPEC_LEN )
    s.csr_valid = BitField( 1 )

    s.pc = BitField( XLEN )
    s.tag = BitField( INST_TAG_LEN )
