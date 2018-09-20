#=========================================================================
# Integer Multiplier Variable Latency RTL Model
#=========================================================================

from pymtl      import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle

# ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define datapath and control unit here.
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#=========================================================================
# Integer Multiplier Variable Latency
#=========================================================================

class IntMulAltPRTL( Model ):

  # Constructor

  def __init__( s ):

    # Interface

    s.req    = InValRdyBundle  ( Bits(64) )
    s.resp   = OutValRdyBundle ( Bits(32) )

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Instantiate datapath and control models here and then connect them
    # together.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  # Line tracing

  def line_trace( s ):

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add additional line tracing using the given line_trace_str for
    # internal state including the current FSM state.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    line_trace_str = ""

    return "{}({}){}".format(
      s.req,
      line_trace_str,
      s.resp,
    )

