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
  def __init__( s, InputType, OutputType, NotifyType, KillType ):
    super( IssueQueueSlotInterface, s ).__init__(
        [
            MethodSpec(
                'valid',
                args=None,
                rets={ 'ret' : Bits(1) },
                call=False,
                rdy=False ),
            MethodSpec(
                'ready',
                args=None,
                rets={ 'ret' : Bits(1) },
                call=False,
                rdy=False ),
            MethodSpec(
                'input',
                args= {'value' : InputType },
                rets=None,
                call=True,
                rdy=False ),
            MethodSpec(
                'output',
                args= None,
                rets={ 'value' : OutputType },
                call=True,
                rdy=False ),
            MethodSpec(
                'notify',
                args= { 'value' : NotifyType },
                rets= None,
                call=True,
                rdy=False ),
            MethodSpec(
                'kill',
                args= { 'value' : KillType },
                rets= None,
                call=True,
                rdy=False ),
        ],
        ordering_chains=[
            [ ],
        ] )


class IssueQueueInterface( Interface ):
  def __init__( s, InputType, OutputType, NotifyType, KillType ):
    super( IssueQueueInterface, s ).__init__(
        [
            MethodSpec(
                'add',
                args= { 'input' : InputType },
                rets=None,
                call=True,
                rdy=True ),
            MethodSpec(
                'remove',
                args=None,
                rets={ 'output' : OutputType },
                call=True,
                rdy=True ),
            MethodSpec(
                'notify',
                args= { 'value' : NotifyType },
                rets= None,
                call=True,
                rdy=False ),
            MethodSpec(
                'kill',
                args= { 'value' : KillType },
                rets= None,
                call=True,
                rdy=False ),
        ],
        ordering_chains=[
            [],
        ] )



class CompactingIssueQueue( Model ):

  def __init__( s, create_slot, InputType, OutputType, NotifyType, KillType,
                num_entries, alloc_nports, issue_nports ):
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
    s.interface = IssueQueueInterface(InputType, OutputType, NotifyType, KillType )
    s.interface.apply(s)

    # Create all the slots in our issue queue
    s._slots = [ create_slot() for _ in range( num_entries ) ]
    # nth entry is shifted from nth slot to n-1 slot
    s._do_shift = [ Wire( 1 ) for _ in range( num_entries ) ]
    s._will_issue = [ Wire( 1 ) for _ in range( num_entries ) ]
    s._slot_select = PriorityDecoder( num_entries )
    s._slot_issue = OneHotEncoder( num_entries )
    s._slot_mux = Mux( OutputType, num_entries )
    s._decode_packer = Packer(Bits(1), s._slot_select.interface.In.nbits )

    # Connect packer into slot decoder
    s.connect(s._slot_select.decode_signal, s._decode_packer.pack_packed)
    # Connect slot select mux to decoder
    s.connect( s._slot_mux.mux_select, s._slot_select.decode_decoded )
    # Also connect slot select mux to onehot encode
    s.connect(s._slot_issue.encode_number, s._slot_select.decode_decoded )

    # Slot shift connection
    for i in range( 1, num_entries ):
      # Enable signal
      s.connect( s._slots[ i - 1 ].input_call , s._do_shift[ i ])
      # Value signal
      s.connect( s._slots[ i ].input_value, s._slots[i+1].output_value )

    # Connect kill and notify signal to each slot
    for i, slot in enumerate( s._slots ):
      # Kill signal
      s.connect( slot.kill_call, s.kill_call )
      s.connect( slot.kill_value, s.kill_value )
      # Notify signal
      s.connect( slot.notify_call, s.notify_call )
      s.connect( slot.notify_value, s.notify_value )
      # Connect slot ready signal to packer
      s.connect( s._decode_packer.pack_in[i], slot.ready_ret)
      # Connect output to mux
      s.connect(s._slot_mux.mux_in[i], s._slots[i].output_value )


    # We call the output method on any slot that should shift or is issuing
    @s.combinational
    def call_output():
      for i, slot in enumerate(s._slots):
        slot.output_call = s._will_issue[i] or s._do_shift[i]

    # Shift if we can
    @s.combinational
    def do_shift():
      s.do_shift[ 0 ] = 0  # Base case
      for i in range( 1, num_entries ):
        # We can only shift if valid and the predecessor is invalid, or issuing
        s.do_shift[ i ].v = not s._will_issue[i] and s.slots[ i ].valid_ret and (
            not s.slots[ i - 1 ].valid_ret or s.will_issue[ i - 1 ] or
            s.do_shift[ i - 1 ] )

    # The add call, to add something to the IQ
    @s.combinational
    def handle_add():
      s.slots[-1 ].input_call = s.add_call
      s.slots[-1 ].input_value = s.add_value
      s.add_rdy = s.do_shift[-1 ] or not s.slots[-1 ].valid_ret or s.will_issue[-1]

    @s.combinational
    def handle_remove():
      s.remove_rdy =  s._slot_select.decode_valid
      s.remove_value = s.slot_mux.mux_out
      for i in range(num_entries):
        s._will_issue[i] = s._slot_select.decode_valid and s.remove_call and s._slot_issue.encode_onehot[i]

  def line_trace( s ):
    return ":".join([ "{}".format( x.out ) for x in s.data ] )
