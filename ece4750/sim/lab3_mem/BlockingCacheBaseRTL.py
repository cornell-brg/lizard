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

from pymtl      import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.ifcs import MemReqMsg4B, MemRespMsg4B
from pclib.ifcs import MemReqMsg16B, MemRespMsg16B

class BlockingCacheBaseVRTL( VerilogModel ):

  vprefix    = "lab3_mem"
  vlinetrace = True

  def __init__( s, num_banks=0 ):

    # Proc <-> Cache

    s.cachereq  = InValRdyBundle ( MemReqMsg4B   )
    s.cacheresp = OutValRdyBundle( MemRespMsg4B  )

    # Cache <-> Mem

    s.memreq    = OutValRdyBundle( MemReqMsg16B  )
    s.memresp   = InValRdyBundle ( MemRespMsg16B )

    # connect to Verilog module

    s.set_params({
      'p_num_banks'   : num_banks
    })

    s.set_ports({
      'clk'           : s.clk,
      'reset'         : s.reset,

      'cachereq_msg'  : s.cachereq.msg,
      'cachereq_val'  : s.cachereq.val,
      'cachereq_rdy'  : s.cachereq.rdy,

      'cacheresp_msg' : s.cacheresp.msg,
      'cacheresp_val' : s.cacheresp.val,
      'cacheresp_rdy' : s.cacheresp.rdy,

      'memreq_msg'    : s.memreq.msg,
      'memreq_val'    : s.memreq.val,
      'memreq_rdy'    : s.memreq.rdy,

      'memresp_msg'   : s.memresp.msg,
      'memresp_val'   : s.memresp.val,
      'memresp_rdy'   : s.memresp.rdy,
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

if   rtl_language == 'pymtl':
  from BlockingCacheBasePRTL import BlockingCacheBasePRTL as BlockingCacheBaseRTL
elif rtl_language == 'verilog':
  BlockingCacheBaseRTL = BlockingCacheBaseVRTL
else:
  raise Exception("Invalid RTL language!")
