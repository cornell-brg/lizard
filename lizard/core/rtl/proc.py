from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from lizard.core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from lizard.core.rtl.memoryflow import MemoryFlowManager, MemoryFlowManagerInterface
from lizard.core.rtl.csr_manager import CSRManager, CSRManagerInterface
from lizard.util.rtl.cam import RandomReplacementCAM, CAMInterface
from lizard.core.rtl.frontend.fetch import Fetch, FetchInterface
from lizard.core.rtl.frontend.decode import Decode, DecodeInterface
from lizard.core.rtl.backend.rename import Rename, RenameInterface
from lizard.core.rtl.backend.issue_selector import IssueSelector
from lizard.core.rtl.backend.issue import Issue, IssueInterface, IssueInOrder, IssueOutOfOrder
from lizard.core.rtl.backend.dispatch import Dispatch, DispatchInterface
from lizard.core.rtl.backend.pipe_selector import PipeSelector
from lizard.core.rtl.backend.alu import ALU
from lizard.core.rtl.backend.branch import Branch, BranchInterface
from lizard.core.rtl.backend.csr import CSR, CSRInterface
from lizard.core.rtl.backend.mem_pipe import MemInterface, Mem
from lizard.core.rtl.backend.m_pipe import MPipe
from lizard.core.rtl.pipeline_arbiter import PipelineArbiter, PipelineArbiterInterface
from lizard.core.rtl.backend.writeback import Writeback, WritebackInterface
from lizard.core.rtl.backend.commit import Commit, CommitInterface
from lizard.core.rtl.messages import ExecuteMsg
from lizard.core.rtl.kill_unit import KillNotifier, RedirectNotifier
from lizard.util import line_block
from lizard.util.line_block import Divider, LineBlock
from lizard.config.general import *


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
    DFLOW_NUM_SRC_PORTS = 2
    DFLOW_NUM_DST_PORTS = 1
    DFLOW_NUM_IS_READY_PORTS = 4
    DFLOW_NUM_FORWARD_PORTS = 1
    ISSUE_NUM_UDPATED_PORTS = DFLOW_NUM_DST_PORTS + DFLOW_NUM_FORWARD_PORTS
    s.dflow_interface = DataFlowManagerInterface(
        XLEN, AREG_COUNT, PREG_COUNT, MAX_SPEC_DEPTH, STORE_QUEUE_SIZE,
        DFLOW_NUM_SRC_PORTS, DFLOW_NUM_DST_PORTS, DFLOW_NUM_IS_READY_PORTS,
        DFLOW_NUM_FORWARD_PORTS)
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
    s.csr_interface = CSRManagerInterface(3, 5)
    s.csr = CSRManager(s.csr_interface)
    s.connect_m(s.db_recv, s.csr.debug_recv)
    s.connect_m(s.db_send, s.csr.debug_send)

    # BTB
    s.btb = RandomReplacementCAM(CAMInterface(XLEN, XLEN), BTB_SIZE)

    # Fetch
    s.fetch_interface = FetchInterface()
    s.fetch = Fetch(s.fetch_interface, MemMsg, ENABLE_BTB)
    s.connect_m(s.mb_recv_0, s.fetch.mem_recv)
    s.connect_m(s.mb_send_0, s.fetch.mem_send)
    s.connect_m(s.cflow.check_redirect, s.fetch.check_redirect)
    s.connect_m(s.btb.read, s.fetch.btb_read)

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
    s.connect_m(s.mflow.register_store, s.rename.mflow_register_store)

    # Split to normal and mem issue queues
    s.issue_selector = IssueSelector()
    s.connect_m(s.issue_selector.in_peek, s.rename.peek)
    s.connect_m(s.issue_selector.in_take, s.rename.take)

    # Issue
    ## Out of Order (OO) Issue
    s.oo_issue_interface = IssueInterface()
    s.oo_issue = Issue(
        s.oo_issue_interface,
        PREG_COUNT,
        NUM_ISSUE_SLOTS,
        ISSUE_NUM_UDPATED_PORTS,
        set_ordered=IssueOutOfOrder,
        bypass_ready=False)

    s.connect_m(s.oo_issue.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.issue_selector.normal_peek, s.oo_issue.in_peek)
    s.connect_m(s.issue_selector.normal_take, s.oo_issue.in_take)
    s.connect_m(s.dflow.is_ready[0], s.oo_issue.is_ready[0])
    s.connect_m(s.dflow.is_ready[1], s.oo_issue.is_ready[1])
    s.connect_m(s.dflow.get_updated, s.oo_issue.get_updated)

    ## In Order (IO) Issue (for memory)
    s.io_issue_interface = IssueInterface()
    s.io_issue = Issue(
        s.io_issue_interface,
        PREG_COUNT,
        NUM_MEM_ISSUE_SLOTS,
        num_updated=ISSUE_NUM_UDPATED_PORTS,
        set_ordered=IssueInOrder,
        bypass_ready=False)
    s.connect_m(s.io_issue.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.issue_selector.mem_peek, s.io_issue.in_peek)
    s.connect_m(s.issue_selector.mem_take, s.io_issue.in_take)
    s.connect_m(s.dflow.is_ready[2], s.io_issue.is_ready[0])
    s.connect_m(s.dflow.is_ready[3], s.io_issue.is_ready[1])
    s.connect_m(s.dflow.get_updated, s.io_issue.get_updated)

    # Dispatch
    ## Dispatch OO
    s.oo_dispatch_interface = DispatchInterface()
    s.oo_dispatch = Dispatch(s.oo_dispatch_interface)
    s.connect_m(s.oo_dispatch.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.oo_issue.peek, s.oo_dispatch.in_peek)
    s.connect_m(s.oo_issue.take, s.oo_dispatch.in_take)
    s.connect_m(s.dflow.read[0], s.oo_dispatch.read[0])
    s.connect_m(s.dflow.read[1], s.oo_dispatch.read[1])

    ## Dispatch IO
    s.io_dispatch_interface = DispatchInterface()
    s.io_dispatch = Dispatch(s.io_dispatch_interface)
    s.connect_m(s.io_dispatch.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.io_issue.peek, s.io_dispatch.in_peek)
    s.connect_m(s.io_issue.take, s.io_dispatch.in_take)
    s.connect_m(s.dflow.read[2], s.io_dispatch.read[0])
    s.connect_m(s.dflow.read[3], s.io_dispatch.read[1])

    # Split
    # Only OO dispatch needs split - IO dispatch goes straight to mem
    s.pipe_selector = PipeSelector()
    s.connect_m(s.pipe_selector.in_peek, s.oo_dispatch.peek)
    s.connect_m(s.pipe_selector.in_take, s.oo_dispatch.take)

    # Execute
    ## ALU
    s.alu = ALU()
    s.connect_m(s.alu.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.alu.in_peek, s.pipe_selector.alu_peek)
    s.connect_m(s.alu.in_take, s.pipe_selector.alu_take)
    s.connect_m(s.alu.forward, s.dflow.forward[0])

    ## Branch
    s.branch_interface = BranchInterface()
    s.branch = Branch(s.branch_interface)
    s.connect_m(s.branch.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.cflow.redirect, s.branch.cflow_redirect)
    s.connect_m(s.branch.in_peek, s.pipe_selector.branch_peek)
    s.connect_m(s.branch.in_take, s.pipe_selector.branch_take)
    s.connect_m(s.btb.write, s.branch.btb_write)

    ## CSR
    s.csr_pipe_interface = CSRInterface()
    s.csr_pipe = CSR(s.csr_pipe_interface)
    s.connect_m(s.csr_pipe.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.csr_pipe.csr_op, s.csr.op)
    s.connect_m(s.csr_pipe.in_peek, s.pipe_selector.csr_peek)
    s.connect_m(s.csr_pipe.in_take, s.pipe_selector.csr_take)

    ## M Pipe
    s.m_pipe = MPipe()
    s.connect_m(s.m_pipe.in_peek, s.pipe_selector.m_pipe_peek)
    s.connect_m(s.m_pipe.in_take, s.pipe_selector.m_pipe_take)
    s.connect_m(s.m_pipe.kill_notify, s.kill_notifier.kill_notify)

    ## Mem
    s.mem_interface = MemInterface()
    s.mem = Mem(s.mem_interface)
    s.connect_m(s.mem.in_peek, s.io_dispatch.peek)
    s.connect_m(s.mem.in_take, s.io_dispatch.take)
    s.connect_m(s.mem.kill_notify, s.kill_notifier.kill_notify)
    s.connect_m(s.mem.store_pending, s.mflow.store_pending)
    s.connect_m(s.mem.send_load, s.mflow.send_load)
    s.connect_m(s.mem.enter_store, s.mflow.enter_store)
    s.connect_m(s.mem.valid_store_mask, s.dflow.valid_store_mask)
    s.connect_m(s.mem.recv_load, s.mflow.recv_load)

    # Writeback Arbiter
    s.writeback_arbiter_interface = PipelineArbiterInterface(ExecuteMsg())
    s.writeback_arbiter = PipelineArbiter(
        s.writeback_arbiter_interface,
        ['mem', 'alu', 'm_pipe', 'branch', 'csr'])
    s.connect_m(s.writeback_arbiter.alu_peek, s.alu.peek)
    s.connect_m(s.writeback_arbiter.alu_take, s.alu.take)
    s.connect_m(s.writeback_arbiter.csr_peek, s.csr_pipe.peek)
    s.connect_m(s.writeback_arbiter.csr_take, s.csr_pipe.take)
    s.connect_m(s.writeback_arbiter.branch_peek, s.branch.peek)
    s.connect_m(s.writeback_arbiter.branch_take, s.branch.take)
    s.connect_m(s.writeback_arbiter.mem_peek, s.mem.peek)
    s.connect_m(s.writeback_arbiter.mem_take, s.mem.take)
    s.connect_m(s.writeback_arbiter.m_pipe_peek, s.m_pipe.peek)
    s.connect_m(s.writeback_arbiter.m_pipe_take, s.m_pipe.take)

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
    s.connect_m(s.commit.dataflow_free_store_id, s.dflow.free_store_id)
    s.connect_m(s.cflow.commit, s.commit.cflow_commit)
    s.connect_m(s.cflow.get_head, s.commit.cflow_get_head)
    s.connect_m(s.commit.send_store, s.mflow.send_store)
    s.connect_m(s.commit.store_acks_outstanding, s.mflow.store_acks_outstanding)
    s.connect_m(s.commit.read_csr, s.csr.read)
    s.connect_m(s.commit.write_csr, s.csr.write)
    s.connect_m(s.commit.btb_clear, s.btb.clear)

  def line_trace(s):
    return line_block.join([
        s.fetch.line_trace(),
        Divider(' | '),
        s.decode.line_trace(),
        Divider(' | '),
        s.rename.line_trace(),
        Divider(' | '),
        LineBlock(
            line_block.join(['O', Divider(': '),
                             s.oo_issue.line_trace()]).normalized().blocks +
            line_block.join(['I', Divider(': '),
                             s.io_issue.line_trace()]).normalized().blocks),
        Divider(' | '),
        LineBlock(
            line_block.join(
                ['O', Divider(': '),
                 s.oo_dispatch.line_trace()]).normalized().blocks + line_block
            .join(['I', Divider(': '),
                   s.io_dispatch.line_trace()]).normalized().blocks),
        Divider(' | '),
        LineBlock(
            line_block.join(['A', Divider(': '),
                             s.alu.line_trace()]).normalized().blocks +
            line_block.join(['B', Divider(': '),
                             s.branch.line_trace()]).normalized().blocks +
            line_block.join(['C', Divider(': '),
                             s.csr_pipe.line_trace()]).normalized().blocks +
            line_block.join([
                'm',
                Divider(': '),
                s.mem.line_trace(),
            ]).normalized().blocks +
            line_block.join(['M', Divider(': '),
                             s.m_pipe.line_trace()]).normalized().blocks),
        Divider(' | '),
        s.writeback.line_trace(),
        Divider(' | '),
        s.commit.line_trace()
    ])
