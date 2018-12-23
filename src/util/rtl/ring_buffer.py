from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import InMethodCallPortBundle


class AllocRequest( BitStructDefinition ):

  def __init__( s, data_size ):
    s.value = BitField( data_size )


class AllocResponse( BitStructDefinition ):

  def __init__( s, data_size ):
    s.index = BitField( data_size )


# Update entry
class UpdateRequest( BitStructDefinition ):

  def __init__( s, idx_size, data_size ):
    s.index = BitField( idx_size )
    s.value = BitField( data_size )


# Peek at the head
class PeekResponse( BitStructDefinition ):

  def __init__( s, data_size ):
    s.value = BitField( data_size )


class RingBuffer( Model ):
  # This stores (key, value) pairs in a finite size FIFO queue
  def __init__( s, NUM_ENTRIES, ENTRY_BITWIDTH ):
    # We want to be a power of two so mod arithmetic is efficient
    IDX_NBITS = clog2( NUM_ENTRIES )
    assert 2**IDX_NBITS == NUM_ENTRIES
    s.head = RegRst( IDX_NBITS, reset_value=0 )
    s.num = RegRst( IDX_NBITS + 1, reset_value=0 )
    s.data = RegEn[ NUM_ENTRIES ]( Bits( ENTRY_BITWIDTH ) )

    s.AllocRequest = AllocRequest( ENTRY_BITWIDTH )
    s.AllocResponse = AllocResponse( ENTRY_BITWIDTH )
    s.UpdateRequest = UpdateRequest( IDX_NBITS, ENTRY_BITWIDTH )
    s.PeekResponse = PeekResponse( IDX_NBITS )

    # These are the methods that can be performed
    s.alloc_port = InMethodCallPortBundle( s.AllocRequest, s.AllocResponse )
    s.update_port = InMethodCallPortBundle( s.UpdateRequest, None, )
    s.remove_port = InMethodCallPortBundle( None, None )
    s.peek_port = InMethodCallPortBundle( None, s.PeekResponse )

    s.num_next = Wire( IDX_NBITS )
    s.next_slot = Wire( IDX_NBITS ) # Index of next slot
    s.empty = Wire(1)

    @s.combinational
    def update():
      s.empty.v = s.num.out == 0

      # Ready signals:
      s.alloc_port.rdy = s.num.out  < NUM_ENTRIES # Alloc rdy
      s.update_port.rdy = not s.empty
      s.remove_port.rdy = not s.empty
      s.peek_port.rdy = not s.empty

      # Default rets
      s.peek_port.ret.value.v = 0
      s.alloc_port.ret.index.v = 0

      # Set enables to regs to false
      for i in range(NUM_ENTRIES):
        s.data[i].en.v = 0

      # Mod arithmetic will handle overflow
      s.next_slot.v = s.head.out + s.num.out
      s.num_next.v = s.num.out
      s.head.in_ = s.head.out

      if s.alloc_port.call: # Alloc an entry
        s.num_next.v += 1  # Incr count
        s.data[ s.next_slot ].in_ = s.alloc_port.arg
        s.alloc_port.ret.index.v = s.next_slot
      if s.update_port.call: # Update an entry
        s.data[ s.update_port.arg.index ].en = 1
        s.data[ s.update_port.arg.index ].in_ = s.update_port.arg.value
      if s.remove_port.call: # Remove head
        s.num_next.v -= 1
        s.head.in_.v = s.head.out + 1
      if s.peek_port.call: # Peek at entry
        s.peek_port.ret.v = s.data[ s.head ].out

      s.num.in_ = s.num_next

  def line_trace( s ):
    return ":".join([ "{}".format( x ) for x in s.data ] )
