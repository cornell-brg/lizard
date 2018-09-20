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
from pclib.ifcs import MemMsg

class MemNetVRTL_inner( VerilogModel ):

  vprefix    = "lab5_mcore"
  modulename = "MemNetVRTL"
  vlinetrace = True

  def __init__( s ):

    # Parameters

    num_reqers    = 4 # 4 data caches
    num_reqees    = 1 # 1 memory port
    num_ports     = max( num_reqers, num_reqees ) # We still have 4 ports

    nopaque_nbits = 8
    mopaque_nbits = 8
    addr_nbits    = 32
    data_nbits    = 128 # MemNet deals with 128 bit refill requests

    # Interface

    s.memifc     = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.mainmemifc = MemMsg( mopaque_nbits, addr_nbits, data_nbits )

    s.memreq_val      = InPort ( 4 )
    s.memreq_rdy      = OutPort( 4 )
    s.memreq_msg      = InPort ( s.memifc.req.nbits * 4)

    s.memresp_val     = OutPort( 4 )
    s.memresp_rdy     = InPort ( 4 )
    s.memresp_msg     = OutPort( s.memifc.resp.nbits * 4)

    s.mainmemreq_val  = OutPort( 4 )
    s.mainmemreq_rdy  = InPort ( 4 )
    s.mainmemreq_msg  = OutPort( s.mainmemifc.req.nbits * 4 )

    s.mainmemresp_val = InPort ( 4 )
    s.mainmemresp_rdy = OutPort( 4 )
    s.mainmemresp_msg = InPort ( s.mainmemifc.resp.nbits * 4 )

    # connect to Verilog module

    s.set_ports({
      'clk'            : s.clk,
      'reset'          : s.reset,

      'memreq_val'     : s.memreq_val,
      'memreq_rdy'     : s.memreq_rdy,
      'memreq_msg'     : s.memreq_msg,

      'memresp_val'    : s.memresp_val,
      'memresp_rdy'    : s.memresp_rdy,
      'memresp_msg'    : s.memresp_msg,

      'mainmemreq_val' : s.mainmemreq_val,
      'mainmemreq_rdy' : s.mainmemreq_rdy,
      'mainmemreq_msg' : s.mainmemreq_msg,

      'mainmemresp_val': s.mainmemresp_val,
      'mainmemresp_rdy': s.mainmemresp_rdy,
      'mainmemresp_msg': s.mainmemresp_msg,
    })

#-------------------------------------------------------------------------
# "Outer" layer PyMTL wrapper
#-------------------------------------------------------------------------

class MemNetVRTL( Model ):

  def __init__( s ):

    # Parameters

    num_reqers    = 4 # 4 data caches
    num_reqees    = 1 # 1 memory port
    num_ports     = max( num_reqers, num_reqees ) # We still have 4 ports

    nopaque_nbits = 8
    mopaque_nbits = 8
    addr_nbits    = 32
    data_nbits    = 128 # MemNet deals with 128 bit refill requests

    # Interface

    s.memifc      = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.mainmemifc  = MemMsg( mopaque_nbits, addr_nbits, data_nbits )

    s.memreq      = InValRdyBundle [num_ports]( s.memifc.req  )
    s.memresp     = OutValRdyBundle[num_ports]( s.memifc.resp )

    s.mainmemreq  = OutValRdyBundle[num_ports]( s.mainmemifc.req  )
    s.mainmemresp = InValRdyBundle [num_ports]( s.mainmemifc.resp )

    # Connection

    s.inner = MemNetVRTL_inner()

    memreq_nbits  = s.memifc.req.nbits
    memresp_nbits = s.memifc.resp.nbits
    mainmemreq_nbits    = s.mainmemifc.req.nbits
    mainmemresp_nbits   = s.mainmemifc.resp.nbits

    for i in xrange(num_ports):
      s.connect_pairs( 
        s.memreq[i].val,  s.inner.memreq_val[i],
        s.memreq[i].rdy,  s.inner.memreq_rdy[i],
        s.memreq[i].msg,  s.inner.memreq_msg[ i*memreq_nbits : (i+1)*memreq_nbits ],

        s.memresp[i].val, s.inner.memresp_val[i],
        s.memresp[i].rdy, s.inner.memresp_rdy[i],
        s.memresp[i].msg, s.inner.memresp_msg[ i*memresp_nbits : (i+1)*memresp_nbits ],

        s.mainmemreq[i].val,    s.inner.mainmemreq_val[i],
        s.mainmemreq[i].rdy,    s.inner.mainmemreq_rdy[i],
        s.mainmemreq[i].msg,    s.inner.mainmemreq_msg[ i*mainmemreq_nbits : (i+1)*mainmemreq_nbits ],

        s.mainmemresp[i].val,   s.inner.mainmemresp_val[i],
        s.mainmemresp[i].rdy,   s.inner.mainmemresp_rdy[i],
        s.mainmemresp[i].msg,   s.inner.mainmemresp_msg[ i*mainmemresp_nbits : (i+1)*mainmemresp_nbits ],
      )

  def line_trace( s ):

    return s.inner.line_trace()

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
  from MemNetPRTL import MemNetPRTL as MemNetRTL
elif rtl_language == 'verilog':
  MemNetRTL = MemNetVRTL
else:
  raise Exception("Invalid RTL language!")
