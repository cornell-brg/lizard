from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR, REG_COUNT
from util.line_block import LineBlock
from copy import deepcopy


class IssueFL( Model ):

  def __init__( s, dataflow, controlflow ):
    s.decoded = InValRdyBundle( DecodePacket() )
    s.issued = OutValRdyBundle( IssuePacket() )

    s.decoded_q = UnbufferedInValRdyQueueAdapter( s.decoded )
    s.issued_q = UnbufferedOutValRdyQueueAdapter( s.issued )

    s.dataflow = dataflow
    s.controlflow = controlflow

    s.out = Wire( IssuePacket() )
    s.out_valid = Wire( 1 )

  def xtick( s ):
    s.decoded_q.xtick()
    s.issued_q.xtick()

    if s.reset:
      s.current_d = None
      s.out_valid.next = 0
      return

    if s.out_valid:
      if not s.issued_q.full():
        s.issued_q.enq( deepcopy( s.out ) )
        s.out_valid.next = 0
        s.current_d = None
      else:
        return

    if s.current_d is None:
      if s.decoded_q.empty():
        return
      s.current_d = s.decoded_q.deq()
      s.work = IssuePacket()
      s.current_rs1 = None
      s.current_rs2 = None
      s.marked_speculative = False

    # verify instruction still alive
    creq = TagValidRequest()
    creq.tag = s.current_d.tag
    cresp = s.controlflow.tag_valid( creq )
    if not cresp.valid:
      # if we allocated a destination register for this instruction,
      # we must free it
      if s.work.rd_valid:
        s.dataflow.free_tag( c.work.rd )
      # retire instruction from controlflow
      creq = RetireRequest()
      creq.tag = s.current_d.tag
      s.controlflow.retire( creq )

      s.current_d = None
      return

    if s.current_d.rs1_valid and s.current_rs1 is None:
      src = s.dataflow.get_src( s.current_d.rs1 )
      s.current_rs1 = src.tag

    if s.current_rs1 is not None and not s.work.rs1_valid:
      read = s.dataflow.read_tag( s.current_rs1 )
      s.work.rs1 = read.value
      s.work.rs1_valid = read.ready

    if s.current_d.rs2_valid and s.current_rs2 is None:
      src = s.dataflow.get_src( s.current_d.rs2 )
      s.current_rs2 = src.tag

    if s.current_rs2 is not None and not s.work.rs2_valid:
      read = s.dataflow.read_tag( s.current_rs2 )
      s.work.rs2 = read.value
      s.work.rs2_valid = read.ready

    # Must get sources before renaming destination!
    # Otherwise consider ADDI x1, x1, 1
    # If you rename the destination first, the instruction is waiting for itself
    if s.current_d.rd_valid and not s.work.rd_valid:
      dst = s.dataflow.get_dst( s.current_d.rd )
      s.work.rd_valid = dst.success
      s.work.rd = dst.tag

    # Done if all fields are as they should be
    if s.current_d.rd_valid == s.work.rd_valid and s.current_d.rs1_valid == s.work.rs1_valid and s.current_d.rs2_valid == s.work.rs2_valid:
      # if the instruction has potential to redirect early (before commit)
      # must declare instruction to controlflow
      # (essentialy creates a rename table snapshot)
      # note this happens after everything else is set -- this instruction
      # must be part of the snapshot
      if not s.marked_speculative and s.current_d.is_branch:
        creq = MarkSpeculativeRequest()
        creq.tag = s.current_d.tag
        cresp = s.controlflow.mark_speculative( creq )
        if cresp.success:
          s.marked_speculative = True
        else:
          # if we failed to mark it speculative
          # (likely because we are too deeply in speculation right now)
          # must stall
          return

      s.work.imm = s.current_d.imm
      s.work.inst = s.current_d.inst
      s.work.csr = s.current_d.csr
      s.work.csr_valid = s.current_d.csr_valid
      s.work.pc = s.current_d.pc
      s.work.tag = s.current_d.tag
      s.work.is_branch = s.current_d.is_branch
      s.out.next = s.work
      s.out_valid.next = 1

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.out.tag ), "{: <8} rd({}): {}".format(
            RV64Inst.name( s.out.inst ), s.out.rd_valid, s.out.rd ),
        "imm: {}".format( s.out.imm ), "rs1({}): {}".format(
            s.out.rs1_valid, s.out.rs1 ), "rs2({}): {}".format(
                s.out.rs2_valid, s.out.rs2 )
    ] ).validate( s.out_valid )
