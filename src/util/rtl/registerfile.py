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
    s.regs_next = [
        [ Wire( dtype ) for _ in range( nregs ) ] for _ in range( wr_ports )
    ]
    s.regs_next_last = [ Wire( dtype ) for _ in range( nregs ) ]
    s.regs_next_dump = [ Wire( dtype ) for _ in range( nregs ) ]

    if reset_values is None:
      reset_values = [ 0 for _ in range( nregs ) ]

    for reg in range( nregs ):
      if wr_ports == 0:

        @s.combinational
        def update_last( reg=reg ):
          s.regs_next_last[ reg ].v = s.regs[ reg ]
      else:

        @s.combinational
        def update_last( reg=reg ):
          s.regs_next_last[ reg ].v = s.regs_next[ wr_ports - 1 ][ reg ]

      if dump_port:
        if combinational_dump_bypass:
          s.connect( s.regs_next_last[ reg ], s.dump_out[ reg ] )
        else:
          s.connect( s.regs[ reg ], s.dump_out[ reg ] )

        @s.combinational
        def update_next_dump( reg=reg ):
          if s.dump_wr_en:
            s.regs_next_dump[ reg ].v = s.dump_in[ reg ]
          else:
            s.regs_next_dump[ reg ].v = s.regs_next_last[ reg ]
      else:

        @s.combinational
        def update_next_dump( reg=reg ):
          s.regs_next_dump[ reg ].v = s.regs_next_last[ reg ]

      @s.tick_rtl
      def update( reg=reg ):
        if s.reset:
          s.regs[ reg ].n = reset_values[ reg ]
        else:
          s.regs[ reg ].n = s.regs_next_dump[ reg ]

    for port in range( rd_ports ):
      if combinational_read_bypass:

        @s.combinational
        def handle_read( port=port ):
          s.rd_data[ port ].v = s.regs_next_dump[ s.rd_addr[ port ] ]
      elif combinational_dump_read_bypass:

        @s.combinational
        def handle_read( port=port ):
          if s.dump_wr_en:
            s.rd_data[ port ].v = s.dump_in[ reg ]
          else:
            s.rd_data[ port ].v = s.regs[ s.rd_addr[ port ] ]
      else:

        @s.combinational
        def handle_read( port=port ):
          s.rd_data[ port ].v = s.regs[ s.rd_addr[ port ] ]

    for reg in range( nregs ):
      for port in range( wr_ports ):

        @s.combinational
        def handle_write( reg=reg, port=port ):
          if s.wr_en[ port ] and s.wr_addr[ port ] == reg:
            s.regs_next[ port ][ reg ].v = s.wr_data[ port ]
          elif port == 0:
            s.regs_next[ port ][ reg ].v = s.regs[ reg ]
          else:
            s.regs_next[ port ][ reg ].v = s.regs_next[ port - 1 ][ reg ]

  def line_trace( s ):
    return ":".join([ "{}".format( x ) for x in s.regs ] )
