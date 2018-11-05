from pymtl import *
from msg.decode import *
from msg.issue import *
from msg.execute import *
from msg.writeback import *
from msg.control import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from util.line_block import LineBlock
from copy import deepcopy


class CommitUnitCL( Model ):

  def __init__( s, dataflow, controlflow, memoryflow ):
    s.result_in_q = InValRdyCLPort( WritebackPacket() )

    s.dataflow = dataflow
    s.controlflow = controlflow
    s.memoryflow = memoryflow

    s.committed = Wire( INST_TAG_LEN )
    s.valid = Wire( 1 )
    # This will be a ring buffer in the RTL
    s.reorder = {}

  def xtick( s ):
    if s.reset:
      s.reorder = {}
      s.valid.next = 0
      return

    # If incoming completed instruction add to reorder buffer
    if s.valid:
      s.valid.next = 0

    # Every cycle ask the control flow if we need to allocate an entry for a new seq number
    seq = s.controlflow.get_curr_seq()
    if ( seq not in s.reorder ):  # Allocate
      s.reorder[ seq ] = None

    if not s.result_in_q.empty():  # Add to reorder
      p = s.result_in_q.deq()
      seq = int( p.tag )
      assert seq in s.reorder
      assert s.reorder[ seq ] is None
      s.reorder[ seq ] = p

    # Every cycle, get the next seq number to be commited
    head = int( s.controlflow.get_head() )
    assert head in s.reorder  # Must be in reorder buffer
    if s.reorder[ head ] is not None:  # we can commit it!
      p = s.reorder[ head ]
      del s.reorder[ head ]  # Free from reorder
      # verify instruction still alive
      creq = TagValidRequest()
      creq.tag = p.tag
      cresp = s.controlflow.tag_valid( creq )
      if not cresp.valid:
        # if we allocated a destination register for this instruction,
        # we must free it
        if p.rd_valid:
          s.dataflow.free_tag( p.rd )
        # retire instruction from controlflow
        creq = RetireRequest()
        creq.tag = p.tag
        s.controlflow.retire( creq )

        # if memory instruction retire
        if p.opcode == Opcode.STORE or p.opcode == Opcode.LOAD:
          s.memoryflow.retire()
        return

      should_commit = True

      # Ready to commit.
      # The instruction might have triggered an exception, in which
      # case it does not commit
      if p.status == PacketStatus.EXCEPTION_TRIGGERED:
        # An exception causes a force redirect
        # to a target specified by the mtvec CSR
        # The mtvec CSR has two fields: MODE
        # and BASE.
        # If MODE is MtvecMode.vectored, the exception jumps to BASE + 4 x mtcause
        # If MODE is MtvecMode.direct, the exception jumps to BASE
        #
        # An exception must also set the mcause and mtval CSR registers
        # with information about the exception
        should_commit = False
        s.dataflow.write_csr( CsrRegisters.mcause, p.mcause )
        s.dataflow.write_csr( CsrRegisters.mtval, p.mtval )
        # TODO: care needs to be taken here, as mepc can never
        # hold a PC value that would cause an instruction-address-misaligned
        # exception. This is done by forcing the 2 low bits to 0
        s.dataflow.write_csr( CsrRegisters.mepc, p.pc )

        # Status is only false if the CSR is a FIFO
        # this only happens for proc2mngr and should not happen now
        mtvec, status = s.dataflow.read_csr( CsrRegisters.mtvec )
        assert status

        mode = mtvec[ 0:2 ]
        base = concat( mtvec[ 2:XLEN ], Bits( 2, 0 ) )
        if mode == MtvecMode.direct:
          target = base
        elif mode == MtvecMode.vectored:
          target = base + ( p.mcause << 2 )
        else:
          # this is a bad state. mtvec is curcial to handling
          # exceptions, and there is no way to handle and exception
          # related to mtvec.
          # In a real processor, this would probably just halt or reset
          # the entire processor
          assert False

        creq = RedirectRequest()
        creq.source_tag = p.tag
        creq.target_pc = target
        creq.at_commit = 1
        creq.force_redirect = 1
        s.controlflow.request_redirect( creq )

        # TODO: the the privledge mode has to be changed to M
        # at this point. Right now, the machine only runs in M
        # however

      if should_commit:
        if p.rd_valid:
          s.dataflow.commit_tag( p.rd )

        # if memory instruction retire
        if p.opcode == Opcode.STORE or p.opcode == Opcode.LOAD:
          s.memoryflow.commit()

      # retire instruction from controlflow
      creq = RetireRequest()
      creq.tag = p.tag
      s.controlflow.retire( creq )
      s.committed.next = p.tag
      s.valid.next = 1

  def line_trace( s ):
    return LineBlock([
        "{}".format( s.committed ),
    ] ).validate( s.valid )
