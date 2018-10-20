from pymtl import *
from msg import MemMsg4B
from msg.fetch import FetchPacket
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import INST_TAG_LEN


class FetchFL( Model ):

  def __init__( s, controlflow ):
    s.mem_req = OutValRdyBundle( MemMsg4B.req )
    s.mem_resp = InValRdyBundle( MemMsg4B.resp )
    s.instrs = OutValRdyBundle( FetchPacket() )

    s.req_q = OutValRdyQueueAdapterFL( s.mem_req )
    s.resp_q = InValRdyQueueAdapterFL( s.mem_resp )
    # output
    s.instrs_q = OutValRdyQueueAdapterFL( s.instrs )

    s.pc = Wire( XLEN )
    s.bad = Wire( 1 )
    s.epoch = Wire( INST_TAG_LEN )

    s.controlflow = controlflow

    @s.tick_fl
    def tick():
      if s.reset:
        s.bad.next = 1
        s.epoch.next = 0
      else:
        if s.bad:
          req = GetEpochStartRequest()
          req.epoch = s.epoch.value
          resp = s.controlflow.get_epoch_start( req )
          if resp.valid:
            s.pc.next = resp.pc
          s.epoch.next = resp.current_epoch
          s.bad.next = not resp.valid
        else:
          s.req_q.append( MemMsg4B.req.mk_rd( 0, s.pc.value, 0 ) )
          mem_resp = s.resp_q.popleft()
          result = FetchPacket()
          result.stat = mem_resp.stat
          result.len = 0
          result.instr = mem_resp.data
          result.pc = s.pc.value

          next_pc = s.pc.value + ILEN_BYTES
          s.pc.next = next_pc

          req = RegisterInstrRequest()
          req.succesor_pc = next_pc
          req.epoch = s.epoch.value
          resp = s.controlflow.register( req )
          if resp.valid:
            result.tag = resp.tag
            s.instrs_q.append( result )
          s.epoch.next = resp.current_epoch
          s.bad.next = not resp.valid

  def line_trace( s ):
    return 'pc: {}'.format( s.pc )
