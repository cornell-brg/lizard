from pymtl import *
from util.rtl.method import InMethodCallPortBundle
from util.rtl.wrap_inc import WrapInc
from util.rtl.registerfile import RegisterFile
from bitutil import clog2, clog2nz


class AllocResponse( BitStructDefinition ):

  def __init__( s, size ):
    s.index = BitField( size )
    s.valid = BitField( 1 )


class FreeRequest( BitStructDefinition ):

  def __init__( s, size ):
    s.index = BitField( size )


class FreeList( Model ):

  def __init__( s,
                nslots,
                num_alloc_ports,
                num_free_ports,
                combinational_bypass,
                used_slots_initial=0 ):

    nbits = clog2nz( nslots )
    ncount_bits = clog2( nslots + 1 )

    s.AllocResponse = AllocResponse( nbits )
    s.FreeRequest = FreeRequest( nbits )

    s.alloc_ports = [
        InMethodCallPortBundle( None, s.AllocResponse, False )
        for _ in range( num_alloc_ports )
    ]
    s.free_ports = [
        InMethodCallPortBundle( s.FreeRequest, None, False )
        for _ in range( num_free_ports )
    ]

    s.free = RegisterFile(
        nbits,
        nslots,
        num_alloc_ports,
        num_free_ports,
        combinational_bypass,
        dump_port=False,
        reset_values=[ x for x in range( nslots ) ] )
    s.size = Wire( ncount_bits )
    s.head = Wire( nbits )
    s.tail = Wire( nbits )

    s.alloc_size_next = [
        Wire( ncount_bits ) for _ in range( num_alloc_ports )
    ]
    s.free_size_next = [ Wire( ncount_bits ) for _ in range( num_free_ports ) ]
    s.bypassed_size = Wire( ncount_bits )
    s.head_next = [ Wire( nbits ) for _ in range( num_alloc_ports ) ]
    s.tail_next = [ Wire( nbits ) for _ in range( num_free_ports ) ]
    s.head_incs = [
        WrapInc( nbits, nslots, True ) for _ in range( num_alloc_ports )
    ]
    s.tail_incs = [
        WrapInc( nbits, nslots, True ) for _ in range( num_free_ports )
    ]

    # PYMTL_BROKEN workaround
    s.workaround_free_ports_arg_index = [
        Wire( nbits ) for _ in range( num_free_ports )
    ]
    for port in range( num_free_ports ):
      s.connect( s.workaround_free_ports_arg_index[ port ],
                 s.free_ports[ port ].arg.index )

    for port in range( num_free_ports ):
      if port == 0:
        s.connect( s.tail_incs[ port ].in_, s.tail )
      else:
        s.connect( s.tail_incs[ port ].in_, s.tail_next[ port - 1 ] )

      @s.combinational
      def handle_free( port=port ):
        if port == 0:
          base = s.size
          ctail = s.tail
        else:
          base = s.free_size_next[ port - 1 ]
          ctail = s.tail_next[ port - 1 ]

        if s.free_ports[ port ].call:
          s.free.wr_en[ port ].v = 1
          s.free.wr_addr[ port ].v = ctail
          # pymtl is broken doesn't translate: https://github.com/cornell-brg/pymtl/issues/141
          # PYMTL_BROKEN
          s.free.wr_data[ port ].v = s.workaround_free_ports_arg_index[ port ]

          s.tail_next[ port ].v = s.tail_incs[ port ].out
          s.free_size_next[ port ].v = base - 1
        else:
          s.free.wr_en[ port ].v = 0
          s.tail_next[ port ].v = ctail
          s.free_size_next[ port ].v = base

    if combinational_bypass:

      @s.combinational
      def handle_bypass():
        s.bypassed_size.v = s.free_size_next[ num_free_ports - 1 ]
    else:

      @s.combinational
      def handle_bypass():
        s.bypassed_size.v = s.size

    # PYMTL_BROKEN workaround
    s.workaround_alloc_ports_ret_valid = [
        Wire( 1 ) for _ in range( num_alloc_ports )
    ]
    for port in range( num_alloc_ports ):
      s.connect( s.workaround_alloc_ports_ret_valid[ port ],
                 s.alloc_ports[ port ].ret.valid )

    for port in range( num_alloc_ports ):
      if port == 0:
        s.connect( s.head_incs[ port ].in_, s.head )
      else:
        s.connect( s.head_incs[ port ].in_, s.head_next[ port - 1 ].out )

      s.connect( s.free.rd_data[ port ], s.alloc_ports[ port ].ret.index )

      @s.combinational
      def handle_alloc( port=port ):
        if port == 0:
          base = s.free_size_next[ num_free_ports - 1 ]
          chead = s.head
        else:
          base = s.alloc_size_next[ port - 1 ]
          chead = s.head_next[ port - 1 ]
        s.free.rd_addr[ port ].v = chead
        if s.alloc_ports[ port ].call and s.bypassed_size != nslots:
          # pymtl is broken doesn't translate: https://github.com/cornell-brg/pymtl/issues/141
          # PYMTL_BROKEN
          s.workaround_alloc_ports_ret_valid[ port ].v = 1
          s.head_next[ port ].v = s.head_incs[ port ].out
          s.alloc_size_next[ port ].v = base + 1
        else:
          # pymtl is broken doesn't translate: https://github.com/cornell-brg/pymtl/issues/141
          # PYMTL_BROKEN
          s.workaround_alloc_ports_ret_valid[ port ].v = 0
          s.head_next[ port ].v = chead
          s.alloc_size_next[ port ].v = base

    @s.tick_rtl
    def update():
      if s.reset:
        s.head.n = used_slots_initial
        s.tail.n = 0
        s.size.n = used_slots_initial
      else:
        s.head.n = s.head_next[ num_alloc_ports - 1 ]
        s.tail.n = s.tail_next[ num_free_ports - 1 ]
        s.size.n = s.alloc_size_next[ num_alloc_ports - 1 ]

  def line_trace( s ):
    return "hd:{}tl:{}:sz:{}:ls:{}".format( s.head.v, s.tail.v, s.size.v,
                                            s.free.line_trace() )
