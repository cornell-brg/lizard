from pymtl import *
from config.general import *
from msg.mem import MemMsgStatus
from msg.packet_common import *


class FetchPacket( BitStructDefinition ):

  def __init__( s ):
    CommonBundle( s )

  def __str__( s ):
    return "{}:{}:{}".format( s.instr, s.pc, s.tag )
