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

class McoreDataCacheVRTL_inner( VerilogModel ):

  vprefix    = "lab5_mcore"
  modulename = "McoreDataCacheVRTL"
  vlinetrace = True

  def __init__( s ):

    # Parameters

    num_cores     = 4
    mopaque_nbits = 8
    addr_nbits    = 32
    data_nbits    = 32
    cacheline_nbits = 128

    # Interface

    s.procifc    = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.mainmemifc = MemMsg( mopaque_nbits, addr_nbits, cacheline_nbits )

    s.procreq_val   = InPort ( num_cores )
    s.procreq_rdy   = OutPort( num_cores )
    s.procreq_msg   = InPort ( s.procifc.req.nbits * num_cores)

    s.procresp_val  = OutPort( num_cores )
    s.procresp_rdy  = InPort ( num_cores )
    s.procresp_msg  = OutPort( s.procifc.resp.nbits * num_cores)

    s.mainmemreq    = OutValRdyBundle( s.mainmemifc.req  )
    s.mainmemresp   = InValRdyBundle ( s.mainmemifc.resp )

    s.dcache_miss   = OutPort( num_cores )
    s.dcache_access = OutPort( num_cores )

    # connect to Verilog module

    s.set_ports({
      'clk'             : s.clk,
      'reset'           : s.reset,

      'procreq_val'     : s.procreq_val,
      'procreq_rdy'     : s.procreq_rdy,
      'procreq_msg'     : s.procreq_msg,

      'procresp_val'    : s.procresp_val,
      'procresp_rdy'    : s.procresp_rdy,
      'procresp_msg'    : s.procresp_msg,

      'mainmemreq_val'  : s.mainmemreq.val,
      'mainmemreq_rdy'  : s.mainmemreq.rdy,
      'mainmemreq_msg'  : s.mainmemreq.msg,

      'mainmemresp_val' : s.mainmemresp.val,
      'mainmemresp_rdy' : s.mainmemresp.rdy,
      'mainmemresp_msg' : s.mainmemresp.msg,

      'dcache_miss'     : s.dcache_miss,
      'dcache_access'   : s.dcache_access,
    })

#-------------------------------------------------------------------------
# "Outer" layer PyMTL wrapper
#-------------------------------------------------------------------------

class McoreDataCacheVRTL( Model ):

  def __init__( s ):

    # Parameters

    num_cores     = 4
    mopaque_nbits = 8
    addr_nbits    = 32
    data_nbits    = 32
    cacheline_nbits = 128

    # Interface

    s.procifc    = MemMsg( mopaque_nbits, addr_nbits, data_nbits )
    s.mainmemifc = MemMsg( mopaque_nbits, addr_nbits, cacheline_nbits )

    s.procreq  = InValRdyBundle [num_cores]( s.procifc.req  )
    s.procresp = OutValRdyBundle[num_cores]( s.procifc.resp )

    s.mainmemreq   = OutValRdyBundle( s.mainmemifc.req  )
    s.mainmemresp  = InValRdyBundle ( s.mainmemifc.resp )

    s.dcache_miss   = OutPort( num_cores )
    s.dcache_access = OutPort( num_cores )

    # Connection

    s.inner = McoreDataCacheVRTL_inner()

    procreq_nbits  = s.procifc.req.nbits
    procresp_nbits = s.procifc.resp.nbits

    for i in xrange(num_cores):
      s.connect_pairs( 
        s.procreq[i].val,  s.inner.procreq_val[i],
        s.procreq[i].rdy,  s.inner.procreq_rdy[i],
        s.procreq[i].msg,  s.inner.procreq_msg[ i*procreq_nbits : (i+1)*procreq_nbits ],

        s.procresp[i].val, s.inner.procresp_val[i],
        s.procresp[i].rdy, s.inner.procresp_rdy[i],
        s.procresp[i].msg, s.inner.procresp_msg[ i*procresp_nbits : (i+1)*procresp_nbits ],

        s.mainmemreq,      s.inner.mainmemreq,
        s.mainmemresp,     s.inner.mainmemresp,

        s.dcache_miss,     s.inner.dcache_miss,
        s.dcache_access,   s.inner.dcache_access,
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
  from McoreDataCachePRTL import McoreDataCachePRTL as McoreDataCacheRTL
elif rtl_language == 'verilog':
  McoreDataCacheRTL = McoreDataCacheVRTL
else:
  raise Exception("Invalid RTL language!")
