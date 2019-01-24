from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import MethodSpec
from util.rtl.coders import PriorityDecoder
from util.rtl.mux import Mux

class IssueSlot( Model ):
  # Must support a ready(), valid(), input(), output(), notify(), kill()
  def __init__():
    pass


class CollapsingIssueQueue( Model ):

  def __init__( s, create_slot, input_type, output_type, notify_type,
                kill_type, num_entries, alloc_nports, issue_nports ):
    """ This model implements a generic issue queue

      create_slot: A function that instatiates a IssueSlot model
                    that conforms to the IssueSlot interface

      input_type: the data type that wil be passed via the input() method
                  to the issue slot
    """
    assert alloc_nports == 1 # Only 1 port supported for now
    assert issue_nports == 1

    s.idx_nbits = clog2( num_entries )
    s.KillDtype = canonicalize_type( kill_dtype )

    # Create all the slots in out issue queue
    s.slots = [ create_slot() for _ in range(num_entries)]

    # nth entry is shift from nth slot to n-1 slot
    s.do_shift = [ Wire(1) for _ in range(num_entries) ]
    s.will_issue = [ Wire(1) for _ in range(num_entries) ]

    s.slot_select = PriorityDecoder(s.idx_nbits)
    s.slot_mux = Mux(output_type, num_entries)

    s.connect(s.slot_mux.mux_in, s.slot_select.decode_decoded)



    # Slot shift connection
    for i in range(1, num_entries):
      # Enable signal
      s.connect(s.do_shift[i], s.slots[i-1].input_call)
      s.connect(s.do_shift[i], s.slots[i].output.call)
      # Value signal
      s.connect(s.slots[i].input_value, s.output_value[i+1])

    # Connect kill and notify signal to each slot
    for i,slot in enumerate(s.slots):
      # Notify signal
      s.connect(slot.kill_call, kill_call)
      s.connect(slot.kill_value, kill_value)
      # Kill signal
      s.connect(slot.notify_call, kill_call)
      s.connect(slot.notify_value, kill_value)
      # Connect ready signal to decoder
      s.connect(slot.ready_ret, s.slot_select.input_value[i])

    # Shift if we can
    @s.combinational
    def do_shift():
      s.do_shift[0] = 1 # Base case
      for i in range(1, num_entries):
        # We can only shift if valid and the predecessor is invalid, or issuing
        s.do_shift[i].v = s.slots[i].valid_ret and (not s.slots[i - 1].valid_ret or s.will_issue[i-1] or s.do_shift[i-1])


    # The add call, to add something to the IQ
    @s.combinational
    def handle_add():
      s.slots[-1].input_call = s.add_call
      s.slots[-1].input_value = s.add_value
      s.add_rdy = s.do_shift[-1] or s.slots[-1].valid_ret


    @s.combinational
    def handle_remove():
      s.remove_rdy = blah # TODO: or of all slot ready signals
      s.remove_value = s.slot_mux.mux_out
      

  def line_trace( s ):
    return ":".join([ "{}".format( x.out ) for x in s.data ] )
