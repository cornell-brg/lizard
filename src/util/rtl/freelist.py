from pymtl import *
from util.rtl.method import MethodSpec
from util.rtl.wrap_inc import WrapInc
from util.rtl.registerfile import RegisterFile
from bitutil import clog2, clog2nz


class FreeListInterface:

  def __init__( s, nslots ):
    nbits = clog2nz( nslots )
    s.Index = Bits( nbits )

    s.alloc = MethodSpec( None, {
        'index': s.Index,
    }, True, True )
    s.free = MethodSpec({
        'index': s.Index,
    }, None, True, False )


class FreeList( Model ):

  def __init__( s,
                nslots,
                num_alloc_ports,
                num_free_ports,
                combinational_bypass,
                used_slots_initial=0 ):
    s.interface = FreeListInterface( nslots )
    ncount_bits = clog2( nslots + 1 )

    s.alloc_ports = [
        s.interface.alloc.in_port() for _ in range( num_alloc_ports )
    ]
    s.free_ports = [
        s.interface.free.in_port() for _ in range( num_free_ports )
    ]

    s.free = RegisterFile(
        s.interface.Index,
        nslots,
        num_alloc_ports,
        num_free_ports,
        combinational_bypass,
        dump_port=False,
        reset_values=[ x for x in range( nslots ) ] )
    s.size = Wire( ncount_bits )
    s.head = Wire( s.interface.Index )
    s.tail = Wire( s.interface.Index )

    s.alloc_size_next = [
        Wire( ncount_bits ) for _ in range( num_alloc_ports )
    ]
    s.free_size_next = [ Wire( ncount_bits ) for _ in range( num_free_ports ) ]
    s.bypassed_size = Wire( ncount_bits )
    s.head_next = [
        Wire( s.interface.Index ) for _ in range( num_alloc_ports )
    ]
    s.tail_next = [ Wire( s.interface.Index ) for _ in range( num_free_ports ) ]
    s.head_incs = [
        WrapInc( s.interface.Index.nbits, nslots, True )
        for _ in range( num_alloc_ports )
    ]
    s.tail_incs = [
        WrapInc( s.interface.Index.nbits, nslots, True )
        for _ in range( num_free_ports )
    ]

    # PYMTL_BROKEN
    s.workaround_tail_incs_inc_out = [
        Wire( s.interface.Index ) for _ in range( num_free_ports )
    ]
    for i in range( num_alloc_ports ):
      s.connect( s.tail_incs[ i ].inc.out, s.workaround_tail_incs_inc_out[ i ] )

    for port in range( num_free_ports ):
      if port == 0:
        s.connect( s.tail_incs[ port ].inc.in_, s.tail )
      else:
        s.connect( s.tail_incs[ port ].inc.in_, s.tail_next[ port - 1 ] )

      @s.combinational
      def handle_free( port=port ):
        if port == 0:
          base = s.size
          ctail = s.tail
        else:
          base = s.free_size_next[ port - 1 ]
          ctail = s.tail_next[ port - 1 ]

        if s.free_ports[ port ].call:
          s.free.wr_ports[ port ].call.v = 1
          s.free.wr_ports[ port ].addr.v = ctail
          s.free.wr_ports[ port ].data.v = s.free_ports[ port ].index

          s.tail_next[ port ].v = s.workaround_tail_incs_inc_out[ port ]
          s.free_size_next[ port ].v = base - 1
        else:
          s.free.wr_ports[ port ].call.v = 0
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

    # PYMTL_BROKEN
    s.workaround_head_incs_inc_out = [
        Wire( s.interface.Index ) for _ in range( num_alloc_ports )
    ]
    for i in range( num_alloc_ports ):
      s.connect( s.head_incs[ i ].inc.out, s.workaround_head_incs_inc_out[ i ] )

    for port in range( num_alloc_ports ):
      if port == 0:
        s.connect( s.head_incs[ port ].inc.in_, s.head )
      else:
        s.connect( s.head_incs[ port ].inc.in_, s.head_next[ port - 1 ].out )

      s.connect( s.free.rd_ports[ port ].data, s.alloc_ports[ port ].index )

      @s.combinational
      def handle_alloc( port=port ):
        if port == 0:
          base = s.free_size_next[ num_free_ports - 1 ]
          chead = s.head
        else:
          base = s.alloc_size_next[ port - 1 ]
          chead = s.head_next[ port - 1 ]
        s.free.rd_ports[ port ].addr.v = chead
        s.alloc_ports[ port ].rdy.v = ( s.bypassed_size != nslots )
        if s.alloc_ports[ port ].call:
          s.head_next[ port ].v = s.workaround_head_incs_inc_out[ port ]
          s.alloc_size_next[ port ].v = base + 1
        else:
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
