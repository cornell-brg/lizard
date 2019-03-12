from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.pipeline_stage import StageInterface, PipelineStageInterface
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from core.rtl.csr_manager import CSRManager, CSRManagerInterface
from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.frontend.decode import Decode, DecodeInterface
from core.rtl.backend.rename import Rename, RenameInterface
from core.rtl.backend.issue import Issue, IssueInterface
from core.rtl.backend.dispatch import Dispatch, DispatchInterface
from core.rtl.backend.pipe_selector import PipeSelector
from core.rtl.backend.alu import ALU, ALUInterface
from core.rtl.backend.csr import CSR, CSRInterface
from core.rtl.pipeline_arbiter import PipelineArbiter
from core.rtl.backend.writeback import Writeback
from core.rtl.backend.commit import Commit
from core.rtl.proc_debug_bus import ProcDebugBusInterface
from core.rtl.messages import *
from mem.rtl.memory_bus import MemoryBusInterface
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
            'mb_recv_0',
            args=None,
            rets={'msg': MemMsg.resp},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'mb_send_0',
            args={'msg': MemMsg.req},
            rets=None,
            call=True,
            rdy=True,
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

    # Dataflow
    s.dflow_interface = DataFlowManagerInterface(XLEN, AREG_COUNT, PREG_COUNT,
                                                 MAX_SPEC_DEPTH, 2, 1)
    s.dflow = DataFlowManager(s.dflow_interface)

    # Control flow
    s.cflow_interface = ControlFlowManagerInterface(
        XLEN, INST_IDX_NBITS, SPEC_IDX_NBITS, SPEC_MASK_NBITS)
    s.cflow = ControlFlowManager(s.cflow_interface, RESET_VECTOR)
    s.connect_m(s.cflow.dflow_snapshot, s.dflow.snapshot)
    s.connect_m(s.cflow.dflow_restore, s.dflow.restore)
    s.connect_m(s.cflow.dflow_free_snapshot, s.dflow.free_snapshot)
    s.connect_m(s.cflow.dflow_rollback, s.dflow.rollback)

    # CSR
    s.csr_interface = CSRManagerInterface()
    s.csr = CSRManager(s.csr_interface)
    s.connect_m(s.db_recv, s.csr.debug_recv)
    s.connect_m(s.db_send, s.csr.debug_send)

    # Fetch
    s.fetch_interface = FetchInterface(XLEN, ILEN)
    s.fetch = Fetch(s.fetch_interface, MemMsg)
    s.connect_m(s.mb_recv_0, s.fetch.mem_recv)
    s.connect_m(s.mb_send_0, s.fetch.mem_send)
    s.connect_m(s.cflow.check_redirect, s.fetch.check_redirect)

    # Decode
    s.decode_interface = DecodeInterface()
    s.decode = Decode(s.decode_interface)
    s.connect_m(s.fetch.get, s.decode.fetch_get)
    s.connect_m(s.cflow.check_redirect, s.decode.check_redirect)

    # Rename
    s.rename_interface = RenameInterface()
    s.rename = Rename(s.rename_interface)
    s.connect_m(s.decode.peek, s.rename.decode_peek)
    s.connect_m(s.decode.take, s.rename.decode_take)
    s.connect_m(s.cflow.register, s.rename.register)
    s.connect_m(s.dflow.get_src[0], s.rename.get_src[0])
    s.connect_m(s.dflow.get_src[1], s.rename.get_src[1])
    s.connect_m(s.dflow.get_dst[0], s.rename.get_dst)

    # Issue
    s.issue_interface = IssueInterface()
    s.issue = Issue(s.issue_interface, PREG_COUNT, num_slots=1)
    s.connect_m(s.rename.get, s.issue.rename_get)
    s.connect_m(s.dflow.is_ready, s.issue.is_ready)
    s.connect_m(s.dflow.get_updated, s.issue.get_updated)

    # Dispatch
    s.dispatch_interface = DispatchInterface()
    s.dispatch = Dispatch(s.dispatch_interface)
    s.connect_m(s.issue.get, s.dispatch.issue_get)
    s.connect_m(s.dflow.read, s.dispatch.read)

    # Split
    s.pipe_selector = PipeSelector()
    s.connect_m(s.pipe_selector.dispatch_get, s.dispatch.get)

    # Execute
    ## ALU
    s.alu_interface = ALUInterface(XLEN)
    s.alu = ALU(s.alu_interface)
    s.connect_m(s.alu.dispatch_get, s.pipe_selector.alu_get)

    ## CSR
    s.csr_pipe_interface = CSRInterface()
    s.csr_pipe = CSR(s.csr_pipe_interface)
    s.connect_m(s.csr_pipe.csr_op, s.csr.op)
    s.connect_m(s.csr_pipe.dispatch_get, s.pipe_selector.csr_get)

    # Writeback Arbiter
    s.writeback_arbiter_interface = PipelineStageInterface(ExecuteMsg())
    s.writeback_arbiter = PipelineArbiter(s.writeback_arbiter_interface,
                                          ['alu', 'csr'])
    s.connect_m(s.writeback_arbiter.alu_peek, s.alu.peek)
    s.connect_m(s.writeback_arbiter.alu_take, s.alu.take)
    s.connect_m(s.writeback_arbiter.csr_peek, s.csr_pipe.peek)
    s.connect_m(s.writeback_arbiter.csr_take, s.csr_pipe.take)

    # Writeback
    s.writeback_interface = StageInterface(ExecuteMsg(), WritebackMsg())
    s.writeback = Writeback(s.writeback_interface)
    s.connect_m(s.writeback_arbiter.peek, s.writeback.in_peek)
    s.connect_m(s.writeback_arbiter.take, s.writeback.in_take)
    s.connect_m(s.writeback.dataflow_write, s.dflow.write[0])

    # Commit
    s.commit_interface = StageInterface(WritebackMsg(), None)
    s.commit = Commit(s.commit_interface, ROB_SIZE)
    s.connect_m(s.writeback.peek, s.commit.in_peek)
    s.connect_m(s.writeback.take, s.commit.in_take)
    s.connect_m(s.commit.dataflow_commit, s.dflow.commit[0])
    s.connect_m(s.cflow.commit, s.commit.cflow_commit)
    s.connect_m(s.cflow.get_head, s.commit.cflow_get_head)
