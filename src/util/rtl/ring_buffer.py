from pymtl import *
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from util.rtl.method import InMethodCallPortBundle


class AllocRequest( BitStructDefinition ):

  def __init__( s, data_size ):
    s.value = BitField( data_size )


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
    s.head = RegEnRst( IDX_NBITS, reset_value=0 )
    s.num = RegRst( IDX_NBITS, reset_value=0 )
    s.data = RegEn[ NUM_ENTRIES ]( Bits( ENTRY_BITWIDTH ) )

    s.ALLOC_REQUEST = AllocRequest( ENTRY_BITWIDTH )
    s.UPDATE_REQUEST = UpdateRequest( IDX_NBITS, ENTRY_BITWIDTH )
    s.PEEK_RESPONSE = PeekResponse( IDX_NBITS )

    # These are the methods that can be performed
    s.ALLOC_PORT = InMethodCallPortBundle( s.ALLOC_REQUEST, None )
    s.UPDATE_PORT = InMethodCallPortBundle( s.UPDATE_REQUEST, None )
    s.REMOVE_PORT = InMethodCallPortBundle( None, None )
    s.PEEK_PORT = InMethodCallPortBundle( None, s.PEEK_RESPONSE )

    s.n_add = Wire( IDX_NBITS )
    s.next_slot = Wire( IDX_NBITS )
    s.access_idx = Wire( IDX_NBITS )

    @s.combinational
    def update():
      # Mod arithmetic will handle overflow
      s.next_slot.v = s.head.out + s.num.out
      s.n_add.v = s.num.out
      s.head.en.v = 0
      # Allocate a entry
      if s.ALLOC_PORT.call:
        s.n_add.v += 1  # Incr count
        s.data[ s.next_slot ].in_ = s.ALLOC_PORT.arg.value
      if s.UPDATE_PORT.call:
        s.access_idx.v = s.UPDATE_PORT.arg.index + s.head.out
        s.data[ s.access_idx ].in_ = s.UPDATE_PORT.arg.value
      if s.REMOVE_PORT.call:
        s.head.en.v = 1
        s.n_add.v -= 1
        s.head.in_.v = s.head.out + 1
      if s.PEEK_PORT.call:
        s.PEEK_PORT.ret.v = s.data[ s.head ].out

      s.num.in_ = s.n_add.v

  def line_trace( s ):
    return ":".join([ "{}".format( x ) for x in s.data ] )
