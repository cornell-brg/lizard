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

class MultiCoreVRTL_inner( VerilogModel ):

  vprefix    = "lab5_mcore"
  modulename = "MultiCoreVRTL"
  vlinetrace = True

  def __init__( s ):

    # Parameters

    num_cores     = 4
    mopaque_nbits = 8
    addr_nbits    = 32
    cacheline_nbits = 128

    # Interface

    s.memifc  = MemMsg( mopaque_nbits, addr_nbits, cacheline_nbits )

    s.mngr2proc_val = InPort ( num_cores )
    s.mngr2proc_rdy = OutPort( num_cores )
    s.mngr2proc_msg = InPort ( 32 * num_cores)

    s.proc2mngr_val = OutPort( num_cores )
    s.proc2mngr_rdy = InPort ( num_cores )
    s.proc2mngr_msg = OutPort( 32 * num_cores)

    s.imemreq       = OutValRdyBundle( s.memifc.req  )
    s.imemresp      = InValRdyBundle ( s.memifc.resp )

    s.dmemreq       = OutValRdyBundle( s.memifc.req  )
    s.dmemresp      = InValRdyBundle ( s.memifc.resp )

    s.stats_en      = OutPort( 1 )
    s.commit_inst   = OutPort( num_cores )
    s.icache_miss   = OutPort( num_cores )
    s.icache_access = OutPort( num_cores )
    s.dcache_miss   = OutPort( num_cores )
    s.dcache_access = OutPort( num_cores )

    # connect to Verilog module

    s.set_ports({
      'clk'           : s.clk,
      'reset'         : s.reset,

      'mngr2proc_val' : s.mngr2proc_val,
      'mngr2proc_rdy' : s.mngr2proc_rdy,
      'mngr2proc_msg' : s.mngr2proc_msg,

      'proc2mngr_val' : s.proc2mngr_val,
      'proc2mngr_rdy' : s.proc2mngr_rdy,
      'proc2mngr_msg' : s.proc2mngr_msg,

      'imemreq_val'   : s.imemreq.val,
      'imemreq_rdy'   : s.imemreq.rdy,
      'imemreq_msg'   : s.imemreq.msg,

      'imemresp_val'  : s.imemresp.val,
      'imemresp_rdy'  : s.imemresp.rdy,
      'imemresp_msg'  : s.imemresp.msg,

      'dmemreq_val'   : s.dmemreq.val,
      'dmemreq_rdy'   : s.dmemreq.rdy,
      'dmemreq_msg'   : s.dmemreq.msg,

      'dmemresp_val'  : s.dmemresp.val,
      'dmemresp_rdy'  : s.dmemresp.rdy,
      'dmemresp_msg'  : s.dmemresp.msg,

      'stats_en'      : s.stats_en,
      'commit_inst'   : s.commit_inst,
      'icache_miss'   : s.icache_miss,
      'icache_access' : s.icache_access,
      'dcache_miss'   : s.dcache_miss,
      'dcache_access' : s.dcache_access,
    })

#-------------------------------------------------------------------------
# "Outer" layer PyMTL wrapper
#-------------------------------------------------------------------------

class MultiCoreVRTL( Model ):

  def __init__( s ):

    # Parameters

    num_cores     = 4
    mopaque_nbits = 8
    addr_nbits    = 32
    cacheline_nbits = 128

    # Interface

    s.memifc = MemMsg( mopaque_nbits, addr_nbits, cacheline_nbits )

    s.mngr2proc = InValRdyBundle [num_cores]( 32 )
    s.proc2mngr = OutValRdyBundle[num_cores]( 32 )

    s.imemreq  = OutValRdyBundle( s.memifc.req )
    s.imemresp = InValRdyBundle ( s.memifc.resp )

    s.dmemreq  = OutValRdyBundle( s.memifc.req )
    s.dmemresp = InValRdyBundle ( s.memifc.resp )

    # These ports are for statistics. Basically we want to provide the
    # simulator with some useful signals to let the simulator calculate
    # cache miss rate.

    s.stats_en      = OutPort( 1 )
    s.commit_inst   = OutPort( num_cores )

    s.icache_miss   = OutPort( num_cores )
    s.icache_access = OutPort( num_cores )
    s.dcache_miss   = OutPort( num_cores )
    s.dcache_access = OutPort( num_cores )

    # Connection

    s.inner = MultiCoreVRTL_inner()

    memreq_nbits  = s.memifc.req.nbits
    memresp_nbits = s.memifc.resp.nbits

    for i in xrange(num_cores):
      s.connect_pairs( 
        s.mngr2proc[i].val, s.inner.mngr2proc_val[i],
        s.mngr2proc[i].rdy, s.inner.mngr2proc_rdy[i],
        s.mngr2proc[i].msg, s.inner.mngr2proc_msg[ i*32 : (i+1)*32 ],

        s.proc2mngr[i].val, s.inner.proc2mngr_val[i],
        s.proc2mngr[i].rdy, s.inner.proc2mngr_rdy[i],
        s.proc2mngr[i].msg, s.inner.proc2mngr_msg[ i*32 : (i+1)*32 ],

        s.imemreq,          s.inner.imemreq,
        s.imemresp,         s.inner.imemresp,
        s.dmemreq,          s.inner.dmemreq,
        s.dmemresp,         s.inner.dmemresp,

        s.stats_en,         s.inner.stats_en,
        s.commit_inst,      s.inner.commit_inst,
        s.icache_miss,      s.inner.icache_miss,
        s.icache_access,    s.inner.icache_access,
        s.dcache_miss,      s.inner.dcache_miss,
        s.dcache_access,    s.inner.dcache_access,
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
  from MultiCorePRTL import MultiCorePRTL as MultiCoreRTL
elif rtl_language == 'verilog':
  MultiCoreRTL = MultiCoreVRTL
else:
  raise Exception("Invalid RTL language!")
