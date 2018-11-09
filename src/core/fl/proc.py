from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapter, OutValRdyQueueAdapter
from pclib.fl import BytesMemPortAdapter

from util.tinyrv2_semantics import TinyRV2Semantics
from config.general import *
from msg.mem import MemMsg4B


class ProcFL( Model ):

  def __init__( s, trace_regs=False, num_cores=1 ):
    s.mngr2proc = InValRdyBundle( XLEN )
    s.proc2mngr = OutValRdyBundle( XLEN )

    s.imemreq = OutValRdyBundle( MemMsg4B.req )
    s.imemresp = InValRdyBundle( MemMsg4B.resp )

    s.dmemreq = OutValRdyBundle( MemMsg4B.req )
    s.dmemresp = InValRdyBundle( MemMsg4B.resp )

    s.mngr2proc_q = InValRdyQueueAdapter( s.mngr2proc )
    s.proc2mngr_q = OutValRdyQueueAdapter( s.proc2mngr )

    s.imem = BytesMemPortAdapter( s.imemreq, s.imemresp )
    s.dmem = BytesMemPortAdapter( s.dmemreq, s.dmemresp )

    # Construct the ISA semantics object

    s.isa = TinyRV2Semantics( s.dmem, s.mngr2proc_q, s.proc2mngr_q )

    # Copies of pc and inst for line tracing

    s.pc = Bits( XLEN, RESET_VECTOR )
    s.inst = Bits( ILEN, 0x00000000 )

    s.width = 33

    def reset_trace( c=" " ):
      s.trace = c * s.width

    @s.tick_fl
    def logic():
      if s.reset:
        reset_trace()
        s.isa.reset()
      else:
        reset_trace()
        s.pc = s.isa.PC.uint()
        s.inst = Bits( ILEN, s.imem[ s.pc:s.pc + 4 ] )
        s.trace = "#".ljust( s.width )
        s.isa.execute( s.inst )
        s.trace = "{:0>8x} {: <24}".format( s.pc, s.inst )

  def line_trace( s ):
    return s.trace
