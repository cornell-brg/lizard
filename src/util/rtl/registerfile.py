from pymtl import *
from bitutil import clog2


class RegisterFile( Model ):

  def __init__( s,
                dtype,
                nregs,
                rd_ports,
                wr_ports,
                combinational_read_bypass,
                reset_values=None ):
    addr_nbits = clog2( nregs )
    s.rd_addr = [ InPort( addr_nbits ) for _ in range( rd_ports ) ]
    s.rd_data = [ OutPort( dtype ) for _ in range( rd_ports ) ]

    s.wr_addr = [ InPort( addr_nbits ) for _ in range( wr_ports ) ]
    s.wr_data = [ InPort( dtype ) for _ in range( wr_ports ) ]
    s.wr_en = [ InPort( 1 ) for _ in range( wr_ports ) ]

    s.regs = [ Wire( dtype ) for _ in range( nregs ) ]
    s.regs_next = [
        [ Wire( dtype ) for _ in range( nregs ) ] for _ in range( wr_ports )
    ]

    if reset_values is None:
      reset_values = [ 0 for _ in range( nregs ) ]

    for reg in range( nregs ):

      @s.tick_rtl
      def update( reg=reg ):
        if s.reset:
          s.regs[ reg ].n = reset_values[ reg ]
        else:
          s.regs[ reg ].n = s.regs_next[ wr_ports - 1 ][ reg ]

    for port in range( rd_ports ):
      if combinational_read_bypass:

        @s.combinational
        def handle_read( port=port ):
          s.rd_data[ port ].v = s.regs_next[ wr_ports - 1 ][ s.rd_addr[ port ] ]
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
