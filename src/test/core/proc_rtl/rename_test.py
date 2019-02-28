from pymtl import *
from bitutil import clog2nz
from model.wrapper import wrap_to_rtl, wrap_to_cl
from util.rtl.interface import Interface, UseInterface, IncludeAll
from model.hardware_model import NotReady, Result
from model.test_harness import TestHarness
from core.rtl.frontend.decode import DecodeInterface, Decode
from test.core.proc_rtl.test_controlflow import TestControlFlowManagerFL
from core.rtl.dataflow import DataFlowManagerInterface
from core.fl.dataflow import DataFlowManagerFL
from core.rtl.backend.rename import Rename, RenameInterface
from test.core.proc_rtl.test_decode import TestDecodeFL
from core.rtl.messages import RenameMsg, DecodeMsg, PipelineMsgStatus


class RenameTestHarness(Model):

  def __init__(s, decode_msgs):
    s.td = TestDecodeFL(decode_msgs)
    s.decode = wrap_to_rtl(s.td)
    s.tcf = wrap_to_rtl(
        TestControlFlowManagerFL(64,
                                 RenameMsg().hdr_seq.nbits, 0x200))
    s.dflow_interface = DataFlowManagerInterface(64, 32, 48, 1, 2, 1)
    s.tdf = wrap_to_rtl(DataFlowManagerFL(s.dflow_interface))

    TestHarness(s, Rename(RenameInterface()), True, 'rename.vcd')
    s.connect_m(s.decode.get, s.dut.decode_get)
    s.connect_m(s.tdf.get_src, s.dut.get_src)
    s.connect_m(s.tdf.get_dst[0], s.dut.get_dst)
    s.connect_m(s.tcf.register, s.dut.register)


def mk_dmsg(pc,
            status,
            rd=None,
            rs1=None,
            rs2=None,
            spec=False,
            pc_succ=0,
            exec_data=None):
  ret = DecodeMsg()
  ret.speculative = spec
  ret.pc_succ = pc_succ
  ret.rd_val = rd is not None
  ret.rd = rd if rd is not None else 0
  ret.rs1_val = rs1 is not None
  ret.rs1 = rs1 if rs1 is not None else 0
  ret.rs2_val = rs2 is not None
  ret.rs2 = rs2 if rs2 is not None else 0
  ret.execution_data = exec_data if exec_data is not None else 0
  ret.hdr_status = status
  ret.hdr_pc = pc
  return ret


def test_basic():
  OK = PipelineMsgStatus.PIPELINE_MSG_STATUS_VALID
  EXCEP = PipelineMsgStatus.PIPELINE_MSG_STATUS_EXCEPTION_RAISED

  msgs = [
      mk_dmsg(0, OK),
      mk_dmsg(4, OK, 0x1),
      mk_dmsg(8, OK, 0x2, 0x3),
      mk_dmsg(12, OK, 0x4, 0x5, 0x6),
      mk_dmsg(16, EXCEP, 0x7),
  ]

  rth = RenameTestHarness(msgs)
  rth.vcd_file = "out.vcd"
  dut = wrap_to_cl(rth)
  dut.reset()
  dut.cycle()
  for i in range(len(msgs)):
    ret = dut.get()
    print(ret)
    dut.cycle()
