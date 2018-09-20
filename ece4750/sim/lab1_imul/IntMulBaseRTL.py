#=========================================================================
# Choose PyMTL or Verilog version
#=========================================================================
# Set this variable to 'pymtl' if you are using PyMTL for your RTL design
# (i.e., your design is in IntMultBasePRTL) or set this variable to
# 'verilog' if you are using Verilog for your RTL design (i.e., your
# design is in IntMulBaseVRTL).

rtl_language = 'verilog'

#-------------------------------------------------------------------------
# Do not edit below this line
#-------------------------------------------------------------------------

# This is the PyMTL wrapper for the corresponding Verilog RTL model.

from pymtl        import *
from pclib.ifcs   import InValRdyBundle, OutValRdyBundle

class IntMulBaseVRTL( VerilogModel ):

  # Verilog module setup

  vprefix    = "lab1_imul"
  vlinetrace = True

  # Constructor

  def __init__( s ):

    # Interface

    s.req   = InValRdyBundle  ( Bits(64) )
    s.resp  = OutValRdyBundle ( Bits(32) )

    # Verilog ports

    s.set_ports({
      'clk'         : s.clk,
      'reset'       : s.reset,

      'req_val'     : s.req.val,
      'req_rdy'     : s.req.rdy,
      'req_msg'     : s.req.msg,

      'resp_val'    : s.resp.val,
      'resp_rdy'    : s.resp.rdy,
      'resp_msg'    : s.resp.msg,
    })

# See if the course staff want to force testing a specific RTL language
# for their own testing.

import sys
if hasattr( sys, '_called_from_test' ):

  import pytest
  if pytest.config.getoption('prtl'):
    rtl_language = 'pymtl'
  elif pytest.config.getoption('vrtl'):
    rtl_language = 'pymtl'

# Import the appropriate version based on the rtl_language variable

if rtl_language == 'pymtl':
  from IntMulBasePRTL import IntMulBasePRTL as IntMulBaseRTL
elif rtl_language == 'verilog':
  IntMulBaseRTL = IntMulBaseVRTL

else:
  raise Exception("Invalid RTL language!")

