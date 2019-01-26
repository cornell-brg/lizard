from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.coders import PriorityDecoder
from util.rtl.mux import Mux
from util.rtl.onehot import OneHotEncoder
from util.rtl.packers import Packer, Unpacker
from util.rtl.interface import Interface
from util.rtl.types import Array, canonicalize_type


# Must support a ready(), valid(), input(), output(), notify(), kill()
class IssueQueueSlotInterface( Interface ):

  def __init__( s, SlotType, NotifyType, KillType, nports_notify=1 ):

    super( IssueQueueSlotInterface, s ).__init__([
        MethodSpec(
            'valid',
            args=None,
            rets={ 'ret': Bits( 1 )},
            call=False,
            rdy=False ),
        MethodSpec(
            'ready',
            args=None,
            rets={ 'ret': Bits( 1 )},
            call=False,
            rdy=False ),
        MethodSpec(
            'input',
            args={ 'value': SlotType},
            rets=None,
            call=True,
            rdy=False ),
        MethodSpec(
            'output',
            args=None,
            rets={ 'value': SlotType},
            call=True,
            rdy=False ),
        MethodSpec(
            'notify',
            args={ 'value': NotifyType},
            rets=None,
            call=True,
            rdy=False ),
        MethodSpec(
            'kill',
            args={ 'value': KillType},
            rets=None,
            call=True,
            rdy=False ),
    ],
                                                 ordering_chains=[
                                                     [],
                                                 ] )


class IssueQueueInterface( Interface ):

  def __init__( s, SlotType, NotifyType, KillType ):
    super( IssueQueueInterface, s ).__init__([
        MethodSpec(
            'add', args={ 'value': SlotType}, rets=None, call=True, rdy=True ),
        MethodSpec(
            'remove',
            args=None,
            rets={ 'value': SlotType},
            call=True,
            rdy=True ),
        MethodSpec(
            'notify',
            args={ 'value': NotifyType},
            rets=None,
            call=True,
            rdy=False ),
        MethodSpec(
            'kill',
            args={ 'value': KillType},
            rets=None,
            call=True,
            rdy=False ),
    ],
                                             ordering_chains=[
                                                 [],
                                             ] )


class CompactingIssueQueue( Model ):

  def __init__( s,
                create_slot,
                SlotType,
                NotifyType,
                KillType,
                num_entries,
                alloc_nports=1,
                issue_nports=1 ):
    """ This model implements a generic issue queue

      create_slot: A function that instatiates a IssueSlot model
                    that conforms to the IssueSlot interface

      input_type: the data type that wil be passed via the input() method
                  to the issue slot
    """
    assert alloc_nports == 1  # Only 1 port supported for now
    assert issue_nports == 1

    s.idx_nbits = clog2( num_entries )
    s.KillDtype = canonicalize_type( KillType )
    s.interface = IssueQueueInterface( SlotType, NotifyType, KillType )
    s.interface.apply( s )

    # Create all the slots in our issue queue
    s.slots_ = [ create_slot() for _ in range( num_entries ) ]
    # nth entry is shifted from nth slot to n-1 slot
    s.do_shift_ = [ Wire( 1 ) for _ in range( num_entries ) ]
    s.will_issue_ = [ Wire( 1 ) for _ in range( num_entries ) ]
    s.slot_select_ = PriorityDecoder( num_entries )
    s.slot_issue_ = OneHotEncoder( num_entries )
    s.slot_mux_ = Mux( SlotType, num_entries )
    s.decode_packer_ = Packer( Bits( 1 ), s.slot_select_.interface.In.nbits )

    # Connect packer into slot decoder
    s.connect( s.slot_select_.decode_signal, s.decode_packer_.pack_packed )
    # Connect slot select mux to decoder
    s.connect( s.slot_mux_.mux_select, s.slot_select_.decode_decoded )
    # Also connect slot select mux to onehot encode
    s.connect( s.slot_issue_.encode_number, s.slot_select_.decode_decoded )

    # Slot shift connection
    for i in range( 1, num_entries ):
      # Enable signal
      s.connect( s.slots_[ i - 1 ].input_call, s.do_shift_[ i ] )
      # Value signal
      s.connect( s.slots_[ i - 1 ].input_value, s.slots_[ i ].output_value )

    # Connect kill and notify signal to each slot
    for i in range( num_entries ):
      # Kill signal
      s.connect( s.slots_[ i ].kill_call, s.kill_call )
      s.connect( s.slots_[ i ].kill_value, s.kill_value )
      # Notify signal
      s.connect( s.slots_[ i ].notify_call, s.notify_call )
      s.connect( s.slots_[ i ].notify_value, s.notify_value )
      # Connect slot ready signal to packer
      s.connect( s.decode_packer_.pack_in[ i ], s.slots_[ i ].ready_ret )
      # Connect output to mux
      s.connect( s.slot_mux_.mux_in[ i ], s.slots_[ i ].output_value )

    # We call the output method on any slot that should shift or is issuing
    @s.combinational
    def call_output():
      for i in range( num_entries ):
        s.slots_[ i ].output_call = s.will_issue_[ i ] or s.do_shift_[ i ]

    # Shift if we can
    @s.combinational
    def do_shift():
      s.do_shift_[ 0 ] = 0  # Base case
      for i in range( 1, num_entries ):
        # We can only shift if valid and the predecessor is invalid, or issuing
        s.do_shift_[ i ].v = not s.will_issue_[ i ] and s.slots_[
            i ].valid_ret and ( not s.slots_[ i - 1 ].valid_ret or
                                s.will_issue_[ i - 1 ] or s.do_shift_[ i - 1 ] )

    # The add call, to add something to the IQ
    @s.combinational
    def handle_add():
      s.slots_[-1 ].input_call = s.add_call
      s.slots_[-1 ].input_value = s.add_value
      s.add_rdy = s.do_shift_[
          -1 ] or not s.slots_[-1 ].valid_ret or s.will_issue_[-1 ]

    @s.combinational
    def handle_remove():
      s.remove_rdy = s.slot_select_.decode_valid
      s.remove_value = s.slot_mux_.mux_out
      for i in range( num_entries ):
        s.will_issue_[
            i ] = s.slot_select_.decode_valid and s.remove_call and s.slot_issue_.encode_onehot[
                i ]

  def line_trace( s ):
    return ":".join([ "{}".format( x.out ) for x in s.data ] )
