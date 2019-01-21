from pymtl import *
from util.rtl.method import MethodSpec, canonicalize_type
from bitutil import clog2, clog2nz


class ConnectionInterface:

  def __init__( s, dtype ):
    s.Data = canonicalize_type( dtype )

    s.connect = MethodSpec({
        'src': s.Data,
    }, {
        'dst': s.Data,
    }, False, False )


class Connection( Model ):

  def __init__( s, dtype ):
    s.interface = ConnectionInterface( dtype )
    s.connect_port = s.interface.connect.in_port()

    @s.combinational
    def connect():
      s.connect_port.dst.v = s.connect_port.src

  def line_trace( s ):
    return "{} -> {}".format( s.connect_port.src, s.connect_port.dst )
