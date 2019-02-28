from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from core.rtl.csr_manager import CSRManager, CSRManagerInterface
from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.frontend.decode import Decode, DecodeInterface
from core.rtl.backend.rename import Rename, RenameInterface
from core.rtl.backend.issue import Issue, IssueInterface
from core.rtl.backend.alu import ALU, ALUInterface
from core.rtl.backend.csr import CSR, CSRInterface
from core.rtl.pipeline_arbiter import PipelineArbiterInterface, PipelineArbiter
from core.rtl.backend.writeback import Writeback, WritebackInterface
from core.rtl.backend.commit import Commit, CommitInterface
from core.rtl.proc_debug_bus import ProcDebugBusInterface
from core.rtl.messages import ExecuteMsg
from mem.rtl.memory_bus import MemoryBusInterface
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface
from mem.rtl.memory_bus import MemMsg, MemMsgType
from config.general import *


class ProcInterface(Interface):

  def __init__(s):
    super(ProcInterface, s).__init__([])


class Proc(Model):
  """
         FRONTEND          :                      BACKEND
                           :                             |          |-> |   CSR   | -> |           |
  |       |    |        |  :  |        |    |       |    |          |-> |  BRANCH | -> |           |    |        |
  | Fetch | -> | Decode | -:> | Rename | -> | Issue | -> | Dispatch |-> |   ALU   | -> | Writeback | -> | Commit |
  |_______|    |________|  :  |________|    |_______|    |__________|-> | MUL/DIV | -> |___________|    |________|
                           :

  1. Fetch: Fetch the instruction word
  2. Decode: Determine control signals
  3. Rename: Rename any aregs, and allocate a seq number
  4. Issue: Issue instructions out of order and operands become ready
  5. Dispatch: Read pregs from RF (or maybe get from bypass network)
  6. Execute: Obvious
  7. Writeback: Write the result into the pref
  8. Commit: Reorder the instruction in a ROB and retire then when they reach the head
  """

  def __init__(s, interface, MemMsg):
    UseInterface(s, interface)
    s.require(
        MethodSpec(
            'mb_recv',
            args=None,
            rets={'msg': MemMsg.resp},
            call=True,
            rdy=True,
            count=2,
        ),
        MethodSpec(
            'mb_send',
            args={'msg': MemMsg.req},
            rets=None,
            call=True,
            rdy=True,
            count=2,
        ),
        MethodSpec(
            'db_recv',
            args=None,
            rets={'msg': Bits(XLEN)},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'db_send',
            args={'msg': Bits(XLEN)},
            rets=None,
            call=True,
            rdy=True,
        ),
    )

    # Control flow
    s.cflow_interface = ControlFlowManagerInterface(XLEN, INST_IDX_NBITS)
    s.cflow = ControlFlowManager(s.cflow_interface, RESET_VECTOR)

    # Dataflow
    s.dflow_interface = DataFlowManagerInterface(XLEN, AREG_COUNT, PREG_COUNT,
                                                 MAX_SPEC_DEPTH, 2, 1)
    s.dflow = DataFlowManager(s.dflow_interface)

    # CSR
    s.csr_interface = CSRManagerInterface()
    s.csr = CSRManager(s.csr_interface)
    s.connect_m(s.db_recv, s.csr.debug_recv)
    s.connect_m(s.db_send, s.csr.debug_send)

    # Mem
    s.mem_controller_interface = BasicMemoryControllerInterface(
        MemMsg, ['fetch'])
    s.mem_controller = BasicMemoryController(s.mem_controller_interface)
    s.connect_m(s.mb_recv[0], s.mem_controller.bus_recv[0])
    s.connect_m(s.mb_send[0], s.mem_controller.bus_send[0])

    # Fetch
    s.fetch_interface = FetchInterface(XLEN, ILEN)
    s.fetch = Fetch(s.fetch_interface, MemMsg)
    s.connect_m(s.mem_controller.fetch_recv, s.fetch.mem_recv)
    s.connect_m(s.mem_controller.fetch_send, s.fetch.mem_send)
    s.connect_m(s.cflow.check_redirect, s.fetch.check_redirect)

    # Decode
    s.decode_interface = DecodeInterface()
    s.decode = Decode(s.decode_interface)
    s.connect_m(s.fetch.get, s.decode.fetch_get)
    s.connect_m(s.cflow.check_redirect, s.decode.check_redirect)

    # Rename
    s.rename_interface = RenameInterface()
    s.rename = Rename(s.rename_interface)
    s.connect_m(s.decode.get, s.rename.decode_get)
    s.connect_m(s.cflow.register, s.rename.register)
    s.connect_m(s.dflow.get_src[0], s.rename.get_src[0])
    s.connect_m(s.dflow.get_src[1], s.rename.get_src[1])
    s.connect_m(s.dflow.get_dst[0], s.rename.get_dst)

    # Issue
    s.issue_interface = IssueInterface()
    s.issue = Issue(s.issue_interface)
    s.connect_m(s.rename.get, s.issue.rename_get)
    s.connect_m(s.dflow.is_ready, s.issue.is_ready)

    # Dispatch
    # TODO

    # Execute
    # TODO

    # Execute.CSR
    s.csr_pipe_interface = CSRInterface()
    s.csr_pipe = CSR(s.csr_pipe_interface)
    s.connect_m(s.csr_pipe.csr_op, s.csr.op)
    # s.connect_m(s.csr_pipe.dispatch_get, s.dispatch...)

    # Writeback Arbiter
    s.writeback_arbiter_interface = PipelineArbiterInterface(ExecuteMsg())
    s.writeback_arbiter = PipelineArbiter(s.writeback_arbiter_interface, 2)
    # s.connect_m(s.writeback_arbiter.in_get[0], ALU)
    s.connect_m(s.writeback_arbiter.in_get[1], s.csr_pipe.get)

    # Writeback
    s.writeback_interface = WritebackInterface()
    s.writeback = Writeback(s.writeback_interface)
    s.connect_m(s.writeback_arbiter.get, s.writeback.execute_get)
    s.connect_m(s.writeback.dataflow_write, s.dflow.write[0])

    # Commit
    s.commit_interface = CommitInterface()
    s.commit = Commit(s.commit_interface)
    s.connect_m(s.writeback.get, s.commit.writeback_get)
    s.connect_m(s.commit.dataflow_commit, s.dflow.commit[0])
