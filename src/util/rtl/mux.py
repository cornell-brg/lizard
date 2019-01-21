from pymtl import *
from util.rtl.method import MethodSpec, canonicalize_type
from bitutil import clog2, clog2nz


class MuxInterface:

  def __init__( s, dtype, nports ):
    s.Data = canonicalize_type( dtype )
    s.Select = Bits( clog2nz( nports ) )

    s.mux = MethodSpec({
        'select': s.Select,
    }, {
        'out': s.Data,
    }, False, False )


class Mux( Model ):

  def __init__( s, dtype, nports ):
    s.interface = MuxInterface( dtype, nports )

    s.in_ = [ InPort( s.interface.Data ) for _ in range( nports ) ]
    s.mux_port = s.interface.mux.in_port()

    @s.combinational
    def select():
      assert s.mux_port.select < nports
      s.mux_port.out.v = s.in_[ s.mux_port.select ]

  def line_trace( s ):
    return "[{}][{}]: {}".format( ', '.join([ str( x ) for x in s.in_ ] ),
                                  s.mux_port.select, s.mux_port.out )
