from pymtl import *
from util.rtl.method import InMethodCallPortBundle
from util.rtl.wrap_inc import WrapInc, WrapDec
from bitutil import clog2


class AllocResponse( BitStructDefinition ):

  def __init__( s, size ):
    s.index = BitField( size )
    s.valid = BitField( 1 )


class FreeRequest( BitStructDefinition ):

  def __init__( s, size ):
    s.index = BitField( size )


class FreeList( Model ):

  def __init__( s, nslots, used_slots_initial=0 ):

    nbits = clog2( nslots )
    s.AllocResponse = AllocResponse( nbits )
    s.FreeRequest = FreeRequest( nbits )

    s.alloc_port = InMethodCallPortBundle( None, s.AllocResponse, False )
    s.free_port = InMethodCallPortBundle( s.FreeRequest, None, False )

    ncount_bits = clog2( nslots + 1 )
    s.free = [ Wire( nbits ) for _ in range( nslots ) ]
    s.size = Wire( ncount_bits )
    s.head = Wire( nbits )
    s.tail = Wire( nbits )

    s.write_idx = Wire( nbits )
    s.write_value = Wire( nbits )
    s.write_en = Wire( 1 )

    s.free_delta = Wire( 1 )
    s.alloc_delta = Wire( 1 )
    s.size_next = Wire( ncount_bits )
    s.size_after_free = Wire( ncount_bits )

    s.head_next = Wire( nbits )
    s.tail_next = Wire( nbits )

    s.head_inc_value = Wire( nbits )
    s.tail_dec_value = Wire( nbits )

    s.head_inc = WrapInc( nbits, nslots )
    s.connect( s.head_inc.in_, s.head )
    s.connect( s.head_inc.out, s.head_inc_value )

    s.tail_dec = WrapDec( nbits, nslots )
    s.connect( s.tail_dec.in_, s.tail )
    s.connect( s.tail_dec.out, s.tail_dec_value )

    for x in range( len( s.free ) ):

      @s.tick_rtl
      def update():
        if s.reset:
          s.free[ x ].n = x
        elif s.write_en and s.write_idx == x:
          s.free[ x ].n = s.write_value

    @s.tick_rtl
    def update():
      if s.reset:
        s.head.n = used_slots_initial
        s.tail.n = 0
        s.size.n = used_slots_initial
      else:
        s.head.n = s.head_next
        s.tail.n = s.tail_next
        s.size.n = s.size_next

    @s.combinational
    def handle_alloc():
      s.alloc_delta.v = 0
      s.head_next.v = s.head
      if s.alloc_port.call:
        if s.size_after_free == nslots:
          s.alloc_port.ret.valid.v = 0
        else:
          s.alloc_port.ret.valid.v = 1
          s.alloc_port.ret.index.v = s.head
          s.alloc_delta.v = 1
          s.head_next.v = s.head_inc_value

    @s.combinational
    def handle_free():
      s.write_en.v = 0
      s.free_delta.v = 0
      s.tail_next.v = s.tail
      s.size_after_free.v = s.size
      if s.free_port.call:
        s.write_idx.v = s.tail
        s.write_value.v = s.free_port.arg.index
        s.write_en.v = 1
        s.free_delta.v = 1
        s.tail_next.v = s.tail_dec_value
        s.size_after_free.v = s.size - 1

    @s.combinational
    def update_size():
      if s.free_delta and s.alloc_delta:
        s.size_next.v = s.size
      elif not s.free_delta and s.alloc_delta:
        s.size_next.v = s.size + 1
      elif s.free_delta and not s.alloc_delta:
        s.size_next.v = s.size - 1
      else:
        s.size_next.v = s.size

  def line_trace( s ):
    return "hd:{}tl:{}:sz:{}".format( s.head.v, s.tail.v, s.size.v )
