from pymtl import *
from mem.rtl.memory_bus import MemMsgType
from core.rtl.messages import MemFunc
from util.rtl.lookup_table import LookupTableInterface, LookupTable
from config.general import *

def MemRequestInterface():
  return StageInterface(DispatchMsg(), DispatchMsg())

class MemRequestStage(Model):
  def __init__(s, interface, MemMsg):
    UseInterface(s, interface)

    s.require(MethodSpec(
          'mb_send',
          args={'msg': MemMsg.req},
          rets=None,
          call=True,
          rdy=True,
    ))

    # Address generation
    s.imm = Wire(DECODED_IMM_LEN)
    s.connect(s.imm, s.process_in_.imm)
    s.sext_imm = Wire(XLEN)
    @s.combinational
    def handle_sext_imm():
      s.sext_imm.v = sext(s.imm, XLEN)
    s.addr = Wire(XLEN)
    @s.combinational
    def compute_addr():
      s.addr.v = s.process_in_.rs1 + s.sext_imm
    

    # Accept a request if the memory bus is ready
    s.connect(s.process_accepted, s.mb_send_rdy)
    # Send a request if we accepted it and are being called
    s.sending_mem_req = Wire(1)
    @s.combinational
    def compute_sending_mem_req():
      s.sending_mem_req.v = s.mb_send_rdy & s.process_call
    s.connect(s.mb_send_call, s.sending_mem_req)

    s.msg_type_lut = LookupTable(LookupTableInterface(MemFunc.bits, MemMsgType.bits), {
      int(MemFunc.MEM_FUNC_LOAD): MemMsgType.READ,
      int(MemFunc.MEM_FUNC_STORE): MemMsgType.WRITE,
    })
    s.connect(s.msg_type_lut.lookup_in_, s.process_in_.mem_msg_func)
    s.connect(s.mb_send_msg.type_, s.msg_type_lut.lookup_out)
    # ignore lookup_valid, it should always be valid
    s.connect(s.mb_send_msg.opaque, 0)
    s.connect(s.mb_send_msg.addr, s.addr)
    # The memory message is 8 bytes, so this is 3 bits
    s.len = Wire(MemMsg.req.len_bits)
    @s.combinational
    def compute_len():
      # The width encoding is:
      # 00: Byte (1)
      # 01: Half word (2)
      # 10: Word (4)
      # 11: Double word (8)
      # so 1 << width will compute that, with 8 overflowing the 0
      # and 0 meaning "all 8 bytes" in the memory message
      s.len = 1 << s.process_in_.mem_msg_width
    s.connect(s.mb_send_msg.len_, s.len)
    # Data always is rs2. If a load, will just be random but doesn't matter
    s.connect(s.mb_send_msg.data, s.rs2)

    # Preserve the message for the next stage when the response comes back
    s.connect(s.process_out, s.process_in_)

def MemResponseInterface()
  return StageInterface(DispatchMsg(), ExecuteMsg())

class MemResponseStage(Model):
  def __init__(s, interface, MemMsg):
    UseInterface(s, interface)
    s.require(MethodSpec(
        'mb_recv',
        args=None,
        rets={'msg': s.MemMsg.resp},
        call=True,
        rdy=True,
    ))

    # Accept it if we have a memory response
    s.connect(s.process_accepted, s.mb_recv_rdy)
    # Take the response if we accepted it and are being called
    s.taking_mem_resp = Wire(1)
    @s.combinational
    def compute_taking_mem_resp():
      s.taking_mem_resp.v = s.mb_recv_rdy & s.process_call
    s.connect(s.mb_recv_call, s.taking_mem_resp)

    s.result = Wire(XLEN)
    @s.combinational
    def compute_result():
      if s.process_in_.mem_msg_func == MemFunc.MEM_FUNC_STORE:
        s.result.v = 0
      elif s.process_in_.mem_msg_unsigned:
        if s.process_in_.mem_msg_width == 0:
          s.result.v = zext(s.mb_recv.data[0:8], XLEN)
        elif s.process_in_.mem_msg_width == 1:
          s.result.v = zext(s.mb_recv.data[0:16], XLEN)
        else:
          s.result.v = zext(s.mb_recv.data[0:32], XLEN)
      else:
        if s.process_in_.mem_msg_width == 0:
          s.result.v = sext(s.mb_recv.data[0:8], XLEN)
        elif s.process_in_.mem_msg_width == 1:
          s.result.v = sext(s.mb_recv.data[0:16], XLEN)
        elif s.process_in_.mem_msg_width == 2:
          s.result.v = sext(s.mb_recv.data[0:32], XLEN)
        else: 
          s.result.v = sext(s.mb_recv.data[0:64], XLEN)
    
    @s.combinational
    def set_process_out():
      s.process_out.v = 0
      s.process_out.hdr.v = s.process_in_.hdr
      s.process_out.result.v = s.result
      s.process_out.rd.v = s.process_in_.rd
      s.process_out.rd_val.v = s.process_in_.rd_val

MemRequest = gen_stage(MemRequestStage)
MemResponse = gen_stage(MemResponseStage)

