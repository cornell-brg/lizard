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

class SingleCoreVRTL( VerilogModel ):

  vprefix    = "lab5_mcore"
  vlinetrace = True

  def __init__( s ):

    # Parameters
    
    num_cores       = 1
    opaque_nbits    = 8
    addr_nbits      = 32
    icache_nbytes   = 256
    dcache_nbytes   = 256
    data_nbits      = 32
    cacheline_nbits = 128

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    s.memifc = MemMsg( opaque_nbits, addr_nbits, cacheline_nbits )

    s.mngr2proc = InValRdyBundle ( 32 )
    s.proc2mngr = OutValRdyBundle( 32 )

    s.imemreq  = OutValRdyBundle( s.memifc.req )
    s.imemresp = InValRdyBundle ( s.memifc.resp )

    s.dmemreq  = OutValRdyBundle( s.memifc.req )
    s.dmemresp = InValRdyBundle ( s.memifc.resp )

    # These ports are for statistics. Basically we want to provide the
    # simulator with some useful signals to let the simulator calculate
    # cache miss rate.

    s.stats_en      = OutPort( 1 )
    s.commit_inst   = OutPort( 1 )

    s.icache_miss   = OutPort( 1 )
    s.icache_access = OutPort( 1 )
    s.dcache_miss   = OutPort( 1 )
    s.dcache_access = OutPort( 1 )

    #---------------------------------------------------------------------
    # Verilog import
    #---------------------------------------------------------------------

    s.set_params({'dummy': 0})

    # connect to Verilog module

    s.set_ports({
      'clk'           : s.clk,
      'reset'         : s.reset,

      'mngr2proc_msg' : s.mngr2proc.msg,
      'mngr2proc_val' : s.mngr2proc.val,
      'mngr2proc_rdy' : s.mngr2proc.rdy,

      'proc2mngr_msg' : s.proc2mngr.msg,
      'proc2mngr_val' : s.proc2mngr.val,
      'proc2mngr_rdy' : s.proc2mngr.rdy,

      'imemreq_msg'   : s.imemreq.msg,
      'imemreq_val'   : s.imemreq.val,
      'imemreq_rdy'   : s.imemreq.rdy,

      'imemresp_msg'  : s.imemresp.msg,
      'imemresp_val'  : s.imemresp.val,
      'imemresp_rdy'  : s.imemresp.rdy,

      'dmemreq_msg'   : s.dmemreq.msg,
      'dmemreq_val'   : s.dmemreq.val,
      'dmemreq_rdy'   : s.dmemreq.rdy,

      'dmemresp_msg'  : s.dmemresp.msg,
      'dmemresp_val'  : s.dmemresp.val,
      'dmemresp_rdy'  : s.dmemresp.rdy,

      'stats_en'      : s.stats_en,
      'commit_inst'   : s.commit_inst,
      'icache_miss'   : s.icache_miss,
      'icache_access' : s.icache_access,
      'dcache_miss'   : s.dcache_miss,
      'dcache_access' : s.dcache_access,
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
  from SingleCorePRTL import SingleCorePRTL as SingleCoreRTL
elif rtl_language == 'verilog':
  SingleCoreRTL = SingleCoreVRTL
else:
  raise Exception("Invalid RTL language!")
