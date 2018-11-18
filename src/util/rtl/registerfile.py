from pymtl import *
from bitutil import clog2, clog2nz


class RegisterFile( Model ):

  def __init__( s,
                dtype,
                nregs,
                rd_ports,
                wr_ports,
                combinational_read_bypass,
                combinational_dump_bypass=False,
                combinational_dump_read_bypass=False,
                dump_port=False,
                reset_values=None ):
    addr_nbits = clog2nz( nregs )
    s.rd_addr = [ InPort( addr_nbits ) for _ in range( rd_ports ) ]
    s.rd_data = [ OutPort( dtype ) for _ in range( rd_ports ) ]

    s.wr_addr = [ InPort( addr_nbits ) for _ in range( wr_ports ) ]
    s.wr_data = [ InPort( dtype ) for _ in range( wr_ports ) ]
    s.wr_en = [ InPort( 1 ) for _ in range( wr_ports ) ]

    if dump_port:
      s.dump_out = [ OutPort( dtype ) for _ in range( nregs ) ]
      s.dump_in = [ InPort( dtype ) for _ in range( nregs ) ]
      s.dump_wr_en = InPort( 1 )

    s.regs = [ Wire( dtype ) for _ in range( nregs ) ]
    # pymtl breaks on translating nested lists due to the dreaded is_lhs
    # error
    # https://github.com/cornell-brg/pymtl/issues/137
    s.regs_next = [ Wire( dtype ) for _ in range( nregs * wr_ports ) ]
    s.regs_next_last = [ Wire( dtype ) for _ in range( nregs ) ]
    s.regs_next_dump = [ Wire( dtype ) for _ in range( nregs ) ]

    if reset_values is None:
      s.reset_values = [ 0 for _ in range( nregs ) ]
    else:
      s.reset_values = reset_values

    # Clean reset values to ensure it is an array of Bits
    # This avoid this pymtl disaster:
    # E       AttributeError:
    # E       Unexpected error during VerilogTranslation!
    # E       Please contact the PyMTL devs!
    # E       'list' object has no attribute 'is_lhs'
    for i in range( nregs ):
      value = s.reset_values[ i ]
      s.reset_values[ i ] = Wire( dtype )
      s.connect( s.reset_values[ i ], value )

    for reg_i in range( nregs ):
      if wr_ports == 0:

        @s.combinational
        def update_last( reg_i=reg_i ):
          s.regs_next_last[ reg_i ].v = s.regs[ reg_i ]
      else:

        @s.combinational
        def update_last( reg_i=reg_i, i=( wr_ports - 1 ) * nregs + reg_i ):
          s.regs_next_last[ reg_i ].v = s.regs_next[ i ]

      if dump_port:
        if combinational_dump_bypass:
          s.connect( s.regs_next_last[ reg_i ], s.dump_out[ reg_i ] )
        else:
          s.connect( s.regs[ reg_i ], s.dump_out[ reg_i ] )

        @s.combinational
        def update_next_dump( reg_i=reg_i ):
          if s.dump_wr_en:
            s.regs_next_dump[ reg_i ].v = s.dump_in[ reg_i ]
          else:
            s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]
      else:

        @s.combinational
        def update_next_dump( reg_i=reg_i ):
          s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

      @s.tick_rtl
      def update( reg_i=reg_i ):
        if s.reset:
          s.regs[ reg_i ].n = s.reset_values[ reg_i ]
        else:
          s.regs[ reg_i ].n = s.regs_next_dump[ reg_i ]

    for port in range( rd_ports ):
      if combinational_read_bypass:

        @s.combinational
        def handle_read( port=port ):
          s.rd_data[ port ].v = s.regs_next_dump[ s.rd_addr[ port ] ]
      elif combinational_dump_read_bypass:

        @s.combinational
        def handle_read( port=port ):
          if s.dump_wr_en:
            s.rd_data[ port ].v = s.dump_in[ reg_i ]
          else:
            s.rd_data[ port ].v = s.regs[ s.rd_addr[ port ] ]
      else:

        @s.combinational
        def handle_read( port=port ):
          s.rd_data[ port ].v = s.regs[ s.rd_addr[ port ] ]

    for reg_i in range( nregs ):
      for port in range( wr_ports ):

        @s.combinational
        def handle_write( reg_i=reg_i,
                          port=port,
                          i=port * nregs + reg_i,
                          j=( port - 1 ) * nregs + reg_i ):
          if s.wr_en[ port ] and s.wr_addr[ port ] == reg_i:
            s.regs_next[ i ].v = s.wr_data[ port ]
          elif port == 0:
            s.regs_next[ i ].v = s.regs[ reg_i ]
          else:
            s.regs_next[ i ].v = s.regs_next[ j ]

  def line_trace( s ):
    return ":".join([ "{}".format( x ) for x in s.regs ] )
