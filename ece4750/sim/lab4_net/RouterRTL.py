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
from pclib.ifcs import NetMsg
from pclib.ifcs import InValRdyBundle, OutValRdyBundle

# Pull in NetHdr from BusNet model
from BusNetRTL import NetHdr

class RouterVRTL_inner( VerilogModel ):

  vprefix    = "lab4_net"
  modulename = "RouterVRTL"
  vlinetrace = True

  # Constructor

  def __init__( s, payload_nbits = 32 ):

    # Interface

    s.router_id        = InPort( 2 )

    s.in0_val          = InPort( 1 )
    s.in0_rdy          = OutPort( 1 )
    s.in0_msg_hdr      = InPort( NetHdr() )
    s.in0_msg_payload  = InPort( payload_nbits )

    s.in1_val          = InPort( 1 )
    s.in1_rdy          = OutPort( 1 )
    s.in1_msg_hdr      = InPort( NetHdr() )
    s.in1_msg_payload  = InPort( payload_nbits )

    s.in2_val          = InPort( 1 )
    s.in2_rdy          = OutPort( 1 )
    s.in2_msg_hdr      = InPort( NetHdr() )
    s.in2_msg_payload  = InPort( payload_nbits )

    s.out0_val         = OutPort( 1 )
    s.out0_rdy         = InPort( 1 )
    s.out0_msg_hdr     = OutPort( NetHdr() )
    s.out0_msg_payload = OutPort( payload_nbits )

    s.out1_val         = OutPort( 1 )
    s.out1_rdy         = InPort( 1 )
    s.out1_msg_hdr     = OutPort( NetHdr() )
    s.out1_msg_payload = OutPort( payload_nbits )

    s.out2_val         = OutPort( 1 )
    s.out2_rdy         = InPort( 1 )
    s.out2_msg_hdr     = OutPort( NetHdr() )
    s.out2_msg_payload = OutPort( payload_nbits )

    # Verilog parameters

    s.set_params({
      'p_payload_nbits'  : payload_nbits,
    })

    # Verilog ports

    s.set_ports({
      'clk'              : s.clk,
      'reset'            : s.reset,

      'router_id'        : s.router_id,

      'in0_val'          : s.in0_val,
      'in0_rdy'          : s.in0_rdy,
      'in0_msg_hdr'      : s.in0_msg_hdr,
      'in0_msg_payload'  : s.in0_msg_payload,

      'in1_val'          : s.in1_val,
      'in1_rdy'          : s.in1_rdy,
      'in1_msg_hdr'      : s.in1_msg_hdr,
      'in1_msg_payload'  : s.in1_msg_payload,

      'in2_val'          : s.in2_val,
      'in2_rdy'          : s.in2_rdy,
      'in2_msg_hdr'      : s.in2_msg_hdr,
      'in2_msg_payload'  : s.in2_msg_payload,

      'out0_val'         : s.out0_val,
      'out0_rdy'         : s.out0_rdy,
      'out0_msg_hdr'     : s.out0_msg_hdr,
      'out0_msg_payload' : s.out0_msg_payload,

      'out1_val'         : s.out1_val,
      'out1_rdy'         : s.out1_rdy,
      'out1_msg_hdr'     : s.out1_msg_hdr,
      'out1_msg_payload' : s.out1_msg_payload,

      'out2_val'         : s.out2_val,
      'out2_rdy'         : s.out2_rdy,
      'out2_msg_hdr'     : s.out2_msg_hdr,
      'out2_msg_payload' : s.out2_msg_payload,
    })

#-------------------------------------------------------------------------
# "Outer" layer PyMTL wrapper
#-------------------------------------------------------------------------

class RouterVRTL( Model ):

  def __init__( s, payload_nbits = 32 ):

    # Parameters
    # Your design does not need to support other values

    num_routers  = 4
    opaque_nbits = 8

    srcdest_nbits = clog2( num_routers )

    # Interface

    s.router_id = InPort( srcdest_nbits )

    msg_type = NetMsg(num_routers, 2**opaque_nbits, payload_nbits)

    s.in0  = InValRdyBundle ( msg_type )
    s.in1  = InValRdyBundle ( msg_type )
    s.in2  = InValRdyBundle ( msg_type )

    s.out0 = OutValRdyBundle( msg_type )
    s.out1 = OutValRdyBundle( msg_type )
    s.out2 = OutValRdyBundle( msg_type )

    # Connection

    s.inner = RouterVRTL_inner(payload_nbits)

    s.in0_hdr  = Wire(NetHdr())
    s.in1_hdr  = Wire(NetHdr())
    s.in2_hdr  = Wire(NetHdr())

    s.out0_hdr = Wire(NetHdr())
    s.out1_hdr = Wire(NetHdr())
    s.out2_hdr = Wire(NetHdr())

    s.connect_pairs( 
      s.in0.msg.dest,     s.in0_hdr.dest,
      s.in0.msg.src,      s.in0_hdr.src,
      s.in0.msg.opaque,   s.in0_hdr.opaque,

      s.in1.msg.dest,     s.in1_hdr.dest,
      s.in1.msg.src,      s.in1_hdr.src,
      s.in1.msg.opaque,   s.in1_hdr.opaque,

      s.in2.msg.dest,     s.in2_hdr.dest,
      s.in2.msg.src,      s.in2_hdr.src,
      s.in2.msg.opaque,   s.in2_hdr.opaque,

      s.out0_hdr.dest,    s.out0.msg.dest,
      s.out0_hdr.src,     s.out0.msg.src,
      s.out0_hdr.opaque,  s.out0.msg.opaque,

      s.out1_hdr.dest,    s.out1.msg.dest,
      s.out1_hdr.src,     s.out1.msg.src,
      s.out1_hdr.opaque,  s.out1.msg.opaque,

      s.out2_hdr.dest,    s.out2.msg.dest,
      s.out2_hdr.src,     s.out2.msg.src,
      s.out2_hdr.opaque,  s.out2.msg.opaque,
    )

    s.connect_pairs( 
      s.router_id,          s.inner.router_id,

      s.in0.val,            s.inner.in0_val,
      s.in0.rdy,            s.inner.in0_rdy,
      s.in0_hdr,            s.inner.in0_msg_hdr,
      s.in0.msg.payload,    s.inner.in0_msg_payload,

      s.in1.val,            s.inner.in1_val,
      s.in1.rdy,            s.inner.in1_rdy,
      s.in1_hdr,            s.inner.in1_msg_hdr,
      s.in1.msg.payload,    s.inner.in1_msg_payload,

      s.in2.val,            s.inner.in2_val,
      s.in2.rdy,            s.inner.in2_rdy,
      s.in2_hdr,            s.inner.in2_msg_hdr,
      s.in2.msg.payload,    s.inner.in2_msg_payload,

      s.out0.val,           s.inner.out0_val,
      s.out0.rdy,           s.inner.out0_rdy,
      s.out0_hdr,           s.inner.out0_msg_hdr,
      s.out0.msg.payload,   s.inner.out0_msg_payload,

      s.out1.val,           s.inner.out1_val,
      s.out1.rdy,           s.inner.out1_rdy,
      s.out1_hdr,           s.inner.out1_msg_hdr,
      s.out1.msg.payload,   s.inner.out1_msg_payload,

      s.out2.val,           s.inner.out2_val,
      s.out2.rdy,           s.inner.out2_rdy,
      s.out2_hdr,           s.inner.out2_msg_hdr,
      s.out2.msg.payload,   s.inner.out2_msg_payload,
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

if rtl_language == 'pymtl':
  from RouterPRTL import RouterPRTL as RouterRTL
elif rtl_language == 'verilog':
  RouterRTL = RouterVRTL 
else:
  raise Exception("Invalid RTL language!")
