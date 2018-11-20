from pymtl import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort, cl_connect


class DelayPipeCL( object ):

  def __init__( s, nstages, in_port, out_port ):
    assert nstages >= 0
    s.in_port = in_port
    s.out_port = out_port
    s.nstages = nstages
    s.data = [ None ] * nstages

    if nstages == 0:
      cl_connect( in_port, out_port )

  def tick( s ):
    if s.nstages == 0:
      return

    # Can we move the first element to the output port?
    if s.data[ 0 ] is not None and not s.out_port.full():
      s.out_port.enq( s.data[ 0 ] )
      s.data[ 0 ] = None

    for i, msg in enumerate( s.data[ 1:] ):
      prev = s.data[ i ]
      if prev is None and msg is not None:  # Shift
        s.data[ i ] = s.data[ i + 1 ]
        s.data[ i + 1 ] = None

    if not s.in_port.empty() and s.data[-1 ] is None:
      s.data[-1 ] = s.in_port.deq()
