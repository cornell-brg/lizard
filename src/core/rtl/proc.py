from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.pipeline_stage import StageInterface, PipelineStageInterface
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from core.rtl.memoryflow import MemoryFlowManager, MemoryFlowManagerInterface
from core.rtl.csr_manager import CSRManager, CSRManagerInterface
from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.frontend.decode import Decode, DecodeInterface
from core.rtl.backend.rename import Rename, RenameInterface
from core.rtl.backend.issue import Issue, IssueInterface
from core.rtl.backend.dispatch import Dispatch, DispatchInterface
from core.rtl.backend.pipe_selector import PipeSelector
from core.rtl.backend.alu import ALU, ALUInterface
from core.rtl.backend.branch import Branch, BranchInterface
from core.rtl.backend.csr import CSR, CSRInterface
from core.rtl.backend.mem_pipe import MemInterface, Mem
from core.rtl.pipeline_arbiter import PipelineArbiter, PipelineArbiterInterface
from core.rtl.backend.writeback import Writeback, WritebackInterface
from core.rtl.backend.commit import Commit, CommitInterface
from core.rtl.proc_debug_bus import ProcDebugBusInterface
from core.rtl.messages import *
from core.rtl.kill_unit import KillNotifier, RedirectNotifier
from mem.rtl.memory_bus import MemoryBusInterface
from mem.rtl.memory_bus import MemMsg, MemMsgType
from util import line_block
from util.line_block import Divider, LineBlock
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
            'mb_recv_1',
            args=None,
            rets={'msg': MemMsg.resp},
            call=True,
            rdy=True,
        ),
        MethodSpec(
            'mb_send_1',
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
    s.dflow_interface = DataFlowManagerInterface(
        XLEN, AREG_COUNT, PREG_COUNT, MAX_SPEC_DEPTH, STORE_QUEUE_SIZE, 2, 1)
    s.dflow = DataFlowManager(s.dflow_interface)

    # Control flow
    s.cflow_interface = ControlFlowManagerInterface(
        XLEN, INST_IDX_NBITS, SPEC_IDX_NBITS, SPEC_MASK_NBITS, STORE_IDX_NBITS)
    s.cflow = ControlFlowManager(s.cflow_interface, RESET_VECTOR)
    s.connect_m(s.cflow.dflow_get_store_id, s.dflow.get_store_id[0])
    s.connect_m(s.cflow.dflow_snapshot, s.dflow.snapshot)
    s.connect_m(s.cflow.dflow_restore, s.dflow.restore)
    s.connect_m(s.cflow.dflow_free_snapshot, s.dflow.free_snapshot)
    s.connect_m(s.cflow.dflow_rollback, s.dflow.rollback)

    # Memory flow
    s.mflow_interface = MemoryFlowManagerInterface(XLEN, MEM_MAX_SIZE,
                                                   STORE_QUEUE_SIZE)
    s.mflow = MemoryFlowManager(s.mflow_interface, MemMsg)
    s.connect_m(s.mb_recv_1, s.mflow.mb_recv)
    s.connect_m(s.mb_send_1, s.mflow.mb_send)

    # Kill notifier
    s.kill_notifier = KillNotifier(s.cflow_interface.KillArgType)
    s.connect_m(s.kill_notifier.check_kill, s.cflow.check_kill)
    s.redirect_notifier = RedirectNotifier(XLEN)
    s.connect_m(s.redirect_notifier.check_redirect, s.cflow.check_redirect)

    # CSR
    s.csr_interface = CSRManagerInterface()
    s.csr = CSRManager(s.csr_interface)
    s.connect_m(s.db_recv, s.csr.debug_recv)
    s.connect_m(s.db_send, s.csr.debug_send)

    # Fetch
    s.fetch_interface = FetchInterface()
    s.fetch = Fetch(s.fetch_interface, MemMsg)
    s.connect_m(s.mb_recv_0, s.fetch.mem_recv)
    s.connect_m(s.mb_send_0, s.fetch.mem_send)
    s.connect_m(s.cflow.check_redirect, s.fetch.check_redirect)

    # Decode
    s.decode_interface = DecodeInterface()
    s.decode = Decode(s.decode_interface)
    s.connect_m(s.decode.kill_notify, s.redirect_notifier.kill_notify)
    s.connect_m(s.fetch.peek, s.decode.in_peek)
    s.connect_m(s.fetch.take, s.decode.in_take)

    # Rename
    s.rename_interface = RenameInterface()
    s.rename = Rename(s.rename_interface)
    s.connect_m(s.rename.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.decode.peek, s.rename.in_peek)
    s.connect_m(s.decode.take, s.rename.in_take)
    s.connect_m(s.cflow.register, s.rename.register)
    s.connect_m(s.dflow.get_src[0], s.rename.get_src[0])
    s.connect_m(s.dflow.get_src[1], s.rename.get_src[1])
    s.connect_m(s.dflow.get_dst[0], s.rename.get_dst)

    # Issue
    s.issue_interface = IssueInterface()
    s.issue = Issue(s.issue_interface, PREG_COUNT, num_slots=NUM_ISSUE_SLOTS)
    s.connect_m(s.issue.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.rename.peek, s.issue.in_peek)
    s.connect_m(s.rename.take, s.issue.in_take)
    s.connect_m(s.dflow.is_ready, s.issue.is_ready)
    s.connect_m(s.dflow.get_updated, s.issue.get_updated)

    # Dispatch
    s.dispatch_interface = DispatchInterface()
    s.dispatch = Dispatch(s.dispatch_interface)
    s.connect_m(s.dispatch.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.issue.peek, s.dispatch.in_peek)
    s.connect_m(s.issue.take, s.dispatch.in_take)
    s.connect_m(s.dflow.read, s.dispatch.read)

    # Split
    s.pipe_selector = PipeSelector()
    s.connect_m(s.pipe_selector.in_peek, s.dispatch.peek)
    s.connect_m(s.pipe_selector.in_take, s.dispatch.take)

    # Execute
    ## ALU
    s.alu_interface = ALUInterface()
    s.alu = ALU(s.alu_interface)
    s.connect_m(s.alu.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.alu.in_peek, s.pipe_selector.alu_peek)
    s.connect_m(s.alu.in_take, s.pipe_selector.alu_take)

    ## Branch
    s.branch_interface = BranchInterface()
    s.branch = Branch(s.branch_interface)
    s.connect_m(s.branch.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.cflow.redirect, s.branch.cflow_redirect)
    s.connect_m(s.branch.in_peek, s.pipe_selector.branch_peek)
    s.connect_m(s.branch.in_take, s.pipe_selector.branch_take)

    ## CSR
    s.csr_pipe_interface = CSRInterface()
    s.csr_pipe = CSR(s.csr_pipe_interface)
    s.connect_m(s.csr_pipe.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.csr_pipe.csr_op, s.csr.op)
    s.connect_m(s.csr_pipe.in_peek, s.pipe_selector.csr_peek)
    s.connect_m(s.csr_pipe.in_take, s.pipe_selector.csr_take)

    ## Mem
    s.mem_interface = MemInterface()
    s.mem = Mem(s.mem_interface)
    s.connect_m(s.mem.in_peek, s.pipe_selector.mem_peek)
    s.connect_m(s.mem.in_take, s.pipe_selector.mem_take)
    s.connect_m(s.mem.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.mem.store_pending, s.mflow.store_pending)
    s.connect_m(s.mem.send_load, s.mflow.send_load)
    s.connect_m(s.mem.enter_store, s.mflow.enter_store)
    s.connect_m(s.mem.valid_store_mask, s.dflow.valid_store_mask)
    s.connect_m(s.mem.recv_load, s.mflow.recv_load)

    # Writeback Arbiter
    s.writeback_arbiter_interface = PipelineArbiterInterface(ExecuteMsg())
    s.writeback_arbiter = PipelineArbiter(s.writeback_arbiter_interface,
                                          ['alu', 'csr', 'branch', 'mem'])
    s.connect_m(s.writeback_arbiter.alu_peek, s.alu.peek)
    s.connect_m(s.writeback_arbiter.alu_take, s.alu.take)
    s.connect_m(s.writeback_arbiter.csr_peek, s.csr_pipe.peek)
    s.connect_m(s.writeback_arbiter.csr_take, s.csr_pipe.take)
    s.connect_m(s.writeback_arbiter.branch_peek, s.branch.peek)
    s.connect_m(s.writeback_arbiter.branch_take, s.branch.take)
    s.connect_m(s.writeback_arbiter.mem_peek, s.mem.peek)
    s.connect_m(s.writeback_arbiter.mem_take, s.mem.take)

    # Writeback
    s.writeback_interface = WritebackInterface()
    s.writeback = Writeback(s.writeback_interface)
    s.connect_m(s.writeback.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.writeback_arbiter.peek, s.writeback.in_peek)
    s.connect_m(s.writeback_arbiter.take, s.writeback.in_take)
    s.connect_m(s.writeback.dataflow_write, s.dflow.write[0])

    # Commit
    s.commit_interface = CommitInterface()
    s.commit = Commit(s.commit_interface, ROB_SIZE)
    s.connect_m(s.commit.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.writeback.peek, s.commit.in_peek)
    s.connect_m(s.writeback.take, s.commit.in_take)
    s.connect_m(s.commit.dataflow_commit, s.dflow.commit[0])
    s.connect_m(s.commit.dataflow_free_store_id, s.dflow.free_store_id[0])
    s.connect_m(s.cflow.commit, s.commit.cflow_commit)
    s.connect_m(s.cflow.get_head, s.commit.cflow_get_head)
    s.connect_m(s.commit.send_store, s.mflow.send_store)

  def line_trace(s):
    return line_block.join([
        s.fetch.line_trace(),
        Divider(' | '),
        s.decode.line_trace(),
        Divider(' | '),
        s.rename.line_trace(),
        Divider(' | '),
        s.issue.line_trace(),
        Divider(' | '),
        s.dispatch.line_trace(),
        Divider(' | '),
        LineBlock(
            line_block.join(['A', Divider(': '),
                             s.alu.line_trace()]).normalized().blocks +
            line_block.join(['B', Divider(': '),
                             s.branch.line_trace()]).normalized().blocks +
            line_block.join(['C', Divider(': '),
                             s.csr_pipe.line_trace()]).normalized().blocks +
            line_block.join([
                'M',
                Divider(': '),
                s.mem.line_trace(),
            ]).normalized().blocks),
        Divider(' | '),
        s.writeback.line_trace(),
        Divider(' | '),
        s.commit.line_trace()
    ])
