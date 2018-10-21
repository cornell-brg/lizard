from pymtl import *
from msg.data import *
from msg.control import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from util.cl.adapters import UnbufferedInValRdyQueueAdapter, UnbufferedOutValRdyQueueAdapter
from config.general import *


class InstrState:

  def __init__( s ):
    s.succesor_pc = Bits( XLEN )
    s.valid = Bits( 1 )
    s.in_flight = Bits( 1 )
    s.rename_table = None

  def __str__( s ):
    return 'spc: {} v: {} f: {} s: {}'.format(
        s.succesor_pc, s.valid, s.in_flight,
        0 if s.rename_table is None else 1 )

  def __repr__( s ):
    return str( s )


class BitDict( dict ):

  def __init__( self, *args, **kwargs ):
    dict.__init__( self, args, **kwargs )

  def __getitem__( self, key ):
    return dict.__getitem__( self, int( key ) )

  def __setitem__( self, key, val ):
    dict.__setitem__( self, int( key ), val )


class ControlFlowUnitFL( Model ):

  def __init__( s, dataflow ):
    s.seq = Bits( INST_TAG_LEN )
    s.head = Bits( INST_TAG_LEN )
    s.epoch = Bits( INST_TAG_LEN )
    s.in_flight = BitDict()
    s.epoch_start = Bits( XLEN )
    s.spec_depth = Bits( MAX_SPEC_DEPTH_LEN )

    s.dataflow = dataflow

  def fl_reset( s ):
    s.seq = 0
    s.head = 0
    s.epoch = 0
    s.in_flight = BitDict()
    s.epoch_start = RESET_VECTOR
    s.spec_depth = 0

  def get_epoch_start( s, request ):
    resp = GetEpochStartResponse()
    resp.current_epoch = s.epoch
    # Only a valid register if issued under a consistent epoch
    resp.valid = ( request.epoch == s.epoch )
    if resp.valid:
      resp.pc = s.epoch_start
    return resp

  def register( s, request ):
    resp = RegisterInstrResponse()
    resp.current_epoch = s.epoch
    # Only a valid register if issued under a consistent epoch
    resp.valid = ( request.epoch == s.epoch )
    if resp.valid:
      resp.tag = s.seq
      s.seq += 1
      state = InstrState()
      state.succesor_pc = request.succesor_pc
      state.valid = 1
      state.in_flight = 1
      state.spec_depth = s.spec_depth
      s.in_flight[ resp.tag ] = state
    return resp

  def mark_speculative( s, request ):
    resp = MarkSpeculativeResponse()
    if s.spec_depth == MAX_SPEC_DEPTH - 1:
      resp.success = 0
    else:
      # increase the speculation depth, and store the rename table
      # from this point
      s.spec_depth += 1
      s.in_flight[ request.tag ].rename_table = s.dataflow.get_rename_table()
      resp.success = 1
    return resp

  def request_redirect( s, request ):
    # if not at commit, and not speculative, error
    assert request.at_commit or s.in_flight[
        request.source_tag ].rename_table is not None
    # the instruction must be valid
    assert s.in_flight[ request.source_tag ].valid

    if s.in_flight[ request.source_tag ].succesor_pc == request.target_pc:
      return

    # invalidate all later instructions
    for tag, state in s.in_flight.iteritems():
      if tag > request.source_tag:
        state.valid = 0
        # if the instruction was speculative free it
        if state.rename_table is not None:
          s.spec_depth -= 1
          state.rename_table = None

    # set a new epoch
    # all new instructions must fall sequentially "into the shadow"
    # of this one
    s.epoch += 1
    s.epoch_start = request.target_pc

    if request.at_commit:
      s.dataflow.rollback_to_arch_state()
    else:
      s.dataflow.set_rename_table(
          s.in_flight[ request.source_tag ].rename_table )

  def tag_valid( s, request ):
    resp = TagValidResponse()
    resp.valid = s.in_flight[ request.tag ].valid
    return resp

  def retire( s, request ):
    s.in_flight[ request.tag ].in_flight = 0

    if s.in_flight[ request.tag ].rename_table is not None:
      s.in_flight[ request.tag ].rename_table = None
      s.spec_depth -= 1

    while s.head < s.seq and s.in_flight[ s.head ].in_flight == 0:
      del s.in_flight[ s.head ]
      s.head += 1
