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

class CacheNetVRTL_inner( VerilogModel ):

  vprefix    = "lab5_mcore"
  modulename = "CacheNetVRTL"
  vlinetrace = True

  def __init__( s ):

    # Parameters

    num_reqers    = 4 # 4 processors
    num_reqees    = 4 # 4 data caches
    num_ports     = max( num_reqers, num_reqees ) # We still have 4 ports

    nopaque_nbits = 8
    mopaque_nbits = 8
    addr_nbits    = 32
    data_nbits    = 32 # CacheNet only deals with 32 bit requests

    # Interface

    s.procifc   = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.cacheifc  = MemMsg( mopaque_nbits, addr_nbits, data_nbits )

    s.procreq_val   = InPort ( 4 )
    s.procreq_rdy   = OutPort( 4 )
    s.procreq_msg   = InPort ( s.procifc.req.nbits * 4)

    s.procresp_val  = OutPort( 4 )
    s.procresp_rdy  = InPort ( 4 )
    s.procresp_msg  = OutPort( s.procifc.resp.nbits * 4)

    s.cachereq_val  = OutPort( 4 )
    s.cachereq_rdy  = InPort ( 4 )
    s.cachereq_msg  = OutPort( s.cacheifc.req.nbits * 4 )

    s.cacheresp_val = InPort ( 4 )
    s.cacheresp_rdy = OutPort( 4 )
    s.cacheresp_msg = InPort ( s.cacheifc.resp.nbits * 4 )

    # connect to Verilog module

    s.set_ports({
      'clk'           : s.clk,
      'reset'         : s.reset,

      'procreq_val'   : s.procreq_val,
      'procreq_rdy'   : s.procreq_rdy,
      'procreq_msg'   : s.procreq_msg,

      'procresp_val'  : s.procresp_val,
      'procresp_rdy'  : s.procresp_rdy,
      'procresp_msg'  : s.procresp_msg,

      'cachereq_val'  : s.cachereq_val,
      'cachereq_rdy'  : s.cachereq_rdy,
      'cachereq_msg'  : s.cachereq_msg,

      'cacheresp_val' : s.cacheresp_val,
      'cacheresp_rdy' : s.cacheresp_rdy,
      'cacheresp_msg' : s.cacheresp_msg,
    })

#-------------------------------------------------------------------------
# "Outer" layer PyMTL wrapper
#-------------------------------------------------------------------------

class CacheNetVRTL( Model ):

  def __init__( s ):

    # Parameters

    num_reqers    = 4 # 4 processors
    num_reqees    = 4 # 4 data caches
    num_ports     = max( num_reqers, num_reqees ) # We still have 4 ports

    nopaque_nbits = 8
    mopaque_nbits = 8
    addr_nbits    = 32
    data_nbits    = 32 # CacheNet only deals with 32 bit requests

    # Interface

    s.procifc   = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.cacheifc  = MemMsg( mopaque_nbits, addr_nbits, data_nbits )

    s.procreq   = InValRdyBundle [num_ports]( s.procifc.req  )
    s.procresp  = OutValRdyBundle[num_ports]( s.procifc.resp )

    s.cachereq  = OutValRdyBundle[num_ports]( s.cacheifc.req  )
    s.cacheresp = InValRdyBundle [num_ports]( s.cacheifc.resp )

    # Connection

    s.inner = CacheNetVRTL_inner()

    procreq_nbits   = s.procifc.req.nbits
    procresp_nbits  = s.procifc.resp.nbits
    cachereq_nbits  = s.cacheifc.req.nbits
    cacheresp_nbits = s.cacheifc.resp.nbits

    for i in xrange(num_ports):
      s.connect_pairs( 
        s.procreq[i].val,   s.inner.procreq_val[i],
        s.procreq[i].rdy,   s.inner.procreq_rdy[i],
        s.procreq[i].msg,   s.inner.procreq_msg[ i*procreq_nbits : (i+1)*procreq_nbits ],

        s.procresp[i].val,  s.inner.procresp_val[i],
        s.procresp[i].rdy,  s.inner.procresp_rdy[i],
        s.procresp[i].msg,  s.inner.procresp_msg[ i*procresp_nbits : (i+1)*procresp_nbits ],

        s.cachereq[i].val,  s.inner.cachereq_val[i],
        s.cachereq[i].rdy,  s.inner.cachereq_rdy[i],
        s.cachereq[i].msg,  s.inner.cachereq_msg[ i*cachereq_nbits : (i+1)*cachereq_nbits ],

        s.cacheresp[i].val, s.inner.cacheresp_val[i],
        s.cacheresp[i].rdy, s.inner.cacheresp_rdy[i],
        s.cacheresp[i].msg, s.inner.cacheresp_msg[ i*cacheresp_nbits : (i+1)*cacheresp_nbits ],
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
  from CacheNetPRTL import CacheNetPRTL as CacheNetRTL
elif rtl_language == 'verilog':
  CacheNetRTL = CacheNetVRTL
else:
  raise Exception("Invalid RTL language!")
