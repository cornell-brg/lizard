from pymtl import *
from msg.decode import *
from msg.data import *
from msg.issue import *
from msg.execute import *
from msg.control import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort, cl_connect
from util.cl.delay_pipe import DelayPipeCL
from util.line_block import LineBlock
from util.arch.semantics import sign
from copy import deepcopy


# The integer execute pipe
class MulDivUnitCL( Model ):
  NCYCLES = 4 # > 0

  def __init__( s, dataflow, controlflow ):
    s.issued_q = InValRdyCLPort( IssuePacket() )
    s.result_q = OutValRdyCLPort( ExecutePacket() )

    # Set up the delay pipe
    source = InValRdyCLPort( ExecutePacket() )
    s.pipe_result_q = OutValRdyCLPort( ExecutePacket() )
    cl_connect( s.pipe_result_q, source)
    s.pipeline = DelayPipeCL(s.NCYCLES-1, source, s.result_q)

    s.dataflow = dataflow
    s.controlflow = controlflow

  def xtick( s ):
    if s.reset:
      pass

    # Is there work to do and pipeline not stalled?
    if not s.issued_q.empty() and not s.pipe_result_q.full():
      s.current = s.issued_q.deq()

      s.work = ExecutePacket()
      copy_common_bundle( s.current, s.work )
      s.work.opcode = s.current.opcode
      copy_field_valid_pair( s.current, s.work, 'rd' )

      if s.current.inst == RV64Inst.MUL:
        s.work.result = Bits(
            XLEN, s.current.rs1.int() * s.current.rs2.int(), trunc=True )
      elif s.current.inst == RV64Inst.MULH:
        s.work.result = Bits(
            XLEN, ( s.current.rs1.int() * s.current.rs2.int() ) >> XLEN,
            trunc=True )
      elif s.current.inst == RV64Inst.MULHU:
        s.work.result = Bits(
            XLEN, ( s.current.rs1.uint() * s.current.rs2.uint() ) >> XLEN,
            trunc=True )
      elif s.current.inst == RV64Inst.MULHSU:
        s.work.result = Bits(
            XLEN, ( s.current.rs1.int() * s.current.rs2.uint() ) >> XLEN,
            trunc=True )
      elif s.current.inst == RV64Inst.DIV:
        if ( s.current.rs2.int() == 0 ):
          s.work.result = Bits( XLEN, -1, trunc=True )
        # Special overflow case
        elif ( s.current.rs1.int() == -2**( XLEN - 1 ) and
               s.current.rs2.int() == -1 ):
          s.work.result = s.current.rs1
        else:
          res = abs( s.current.rs1.int() ) // abs( s.current.rs2.int() )
          sn = sign( s.current.rs1.int() ) * sign( s.current.rs2.int() )
          s.work.result = Bits( XLEN, sn * res, trunc=True )
      elif s.current.inst == RV64Inst.DIVU:
        if ( s.current.rs2.int() == 0 ):
          s.work.result = Bits( XLEN, -1, trunc=True )
        else:
          s.work.result = Bits(
              XLEN, s.current.rs1.uint() // s.current.rs2.uint(), trunc=True )
      elif s.current.inst == RV64Inst.REM:
        s1, s2 = s.current.rs1.int(), s.current.rs2.int()
        if s2 == 0:
          s.work.result = s.current.rs1
        elif s1 == -2**( XLEN - 1 ) and s2 == -1:
          s.work.result = 0
        else:
          res = abs( s1 ) % abs( s2 )
          sn = sign( s1 )
          s.work.result = Bits( XLEN, sn * res, trunc=True )
      elif s.current.inst == RV64Inst.REMU:
        if s.current.rs2.int() == 0:
          s.work.result = s.current.rs1
        else:
          s.work.result = Bits(
              XLEN, s.current.rs1.uint() % s.current.rs2.uint(), trunc=True )
      # W suffix instructions
      elif s.current.inst == RV64Inst.MULW:
        res = (
            s.current.rs1[:32 ].int() * s.current.rs2[:32 ].int() ) & BIT32_MASK
        s.work.result = sext( Bits( 32, res, trunc=True ), XLEN )
      elif s.current.inst == RV64Inst.DIVW:
        s1 = s.current.rs1[:32 ].int()
        s2 = s.current.rs2[:32 ].int()
        if s2 == 0:
          s.work.result = Bits( XLEN, -1, trunc=True )
        # Special overflow case
        elif s1 == -2**( 32 - 1 ) and s2 == -1:
          s.work.result = Bits( XLEN, s1 )
        else:
          res = abs( s1 ) // abs( s2 )
          sn = sign( s1 ) * sign( s2 )
          s.work.result = sext( Bits( 32, sn * res, trunc=True ), XLEN )
      elif s.current.inst == RV64Inst.DIVUW:
        s1 = s.current.rs1[:32 ].uint()
        s2 = s.current.rs2[:32 ].uint()
        if ( s2 == 0 ):
          s.work.result = Bits( XLEN, -1, trunc=True )
        else:
          s.work.result = sext( Bits( 32, s1 // s2, trunc=True ), XLEN )
      elif s.current.inst == RV64Inst.REMW:
        s1 = s.current.rs1[:32 ].int()
        s2 = s.current.rs2[:32 ].int()

        if s2 == 0:
          s.work.result = sext( Bits( 32, s1 ), XLEN )
        # Special overflow case
        elif ( s1 == -2**( 32 - 1 ) and s2 == -1 ):
          s.work.result = Bits( XLEN, 0 )
        else:
          res = abs( s1 ) % abs( s2 )
          sn = sign( s1 )
          s.work.result = sext( Bits( 32, sn * res, trunc=True ), XLEN )
      elif s.current.inst == RV64Inst.REMUW:
        s1 = s.current.rs1[:32 ].uint()
        s2 = s.current.rs2[:32 ].uint()
        if s2 == 0:
          s.work.result = sext( Bits( 32, s1 ), XLEN )
        else:
          s.work.result = sext( Bits( 32, s1 % s2, trunc=True ), XLEN )
      elif s.current.inst == RV64Inst.REMU:
        s1 = s.current.rs1[:32 ].uint()
        s2 = s.current.rs2[:32 ].uint()
        if s1 == 0:
          s.work.result = s1
        else:
          s.work.result = sext( s1 % s2, XLEN )
      else:
        raise NotImplementedError(
            'Not implemented so sad: %x ' % s.current.opcode +
            RV64Inst.name( s.current.inst ) )

      # Output the finished instruction
      s.pipe_result_q.enq( s.work )

    s.pipeline.tick() # Tick our delay pipe

    # Forward from last stage
    if s.result_q.full():
      # Forward
      res = s.result_q.peek()  # Peek at the value in the reg
      if res.rd_valid:
        fwd = PostForwards()
        fwd.tag = res.rd
        fwd.value = res.result
        s.dataflow.forward( fwd )



  def line_trace( s ):
    return LineBlock([
        "{}".format( s.result_q.msg().tag ),
        "{: <8} rd({}): {}".format(
            RV64Inst.name( s.result_q.msg().inst ),
            s.result_q.msg().rd_valid,
            s.result_q.msg().rd ),
        "res: {}".format( s.result_q.msg().result ),
    ] ).validate( s.result_q.val() )
