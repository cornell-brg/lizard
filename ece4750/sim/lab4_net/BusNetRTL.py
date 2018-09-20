#=========================================================================
# Choose PyMTL or Verilog version
#=========================================================================
# Set this variable to 'pymtl' if you are using PyMTL for your RTL design
# (i.e., your design is in IntMultAltPRTL) or set this variable to
# 'verilog' if you are using Verilog for your RTL design (i.e., your
# design is in IntMulAltVRTL).

rtl_language = 'verilog'

#-------------------------------------------------------------------------
# Do not edit below this line
#-------------------------------------------------------------------------

from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.ifcs import NetMsg

class NetHdr( BitStructDefinition ):
  
  def __init__( s ):

    s.dest   = BitField( 2 )
    s.src    = BitField( 2 )
    s.opaque = BitField( 8 )

  def __str__( s ):
    return "{}:{}:{}".format( s.dest, s.src, s.opaque )

class BusNetVRTL_inner( VerilogModel ):

  vprefix    = "lab4_net"
  modulename = "BusNetVRTL"
  vlinetrace = True

  def __init__( s, payload_nbits = 32 ):

    # Interface

    s.in_val          = InPort ( 4 )
    s.in_rdy          = OutPort( 4 )
    s.in_msg_hdr      = InPort( NetHdr().nbits * 4)
    s.in_msg_payload  = InPort( payload_nbits * 4)

    s.out_val         = OutPort( 4 )
    s.out_rdy         = InPort ( 4 )
    s.out_msg_hdr     = OutPort( NetHdr().nbits * 4 )
    s.out_msg_payload = OutPort( payload_nbits * 4)

    # connect to Verilog module

    s.set_params({
      'p_payload_nbits'   : payload_nbits
    })

    s.set_ports({
      'clk'             : s.clk,
      'reset'           : s.reset,

      'in_val'          : s.in_val,
      'in_rdy'          : s.in_rdy,
      'in_msg_hdr'      : s.in_msg_hdr,
      'in_msg_payload'  : s.in_msg_payload,

      'out_val'         : s.out_val,
      'out_rdy'         : s.out_rdy,
      'out_msg_hdr'     : s.out_msg_hdr,
      'out_msg_payload' : s.out_msg_payload,
    })

#-------------------------------------------------------------------------
# "Outer" layer PyMTL wrapper
#-------------------------------------------------------------------------

class BusNetVRTL( Model ):

  def __init__( s, payload_nbits = 32 ):

    # Parameters
    # Your design does not need to support other values

    num_ports    = 4
    opaque_nbits = 8

    # Interface

    s.in_ = InValRdyBundle [num_ports]( NetMsg(num_ports, 2**opaque_nbits, payload_nbits) )
    s.out = OutValRdyBundle[num_ports]( NetMsg(num_ports, 2**opaque_nbits, payload_nbits) )

    # Connection

    s.inner = BusNetVRTL_inner(payload_nbits)

    s.in_hdrs  = [Wire(NetHdr()) for _ in xrange(num_ports)]
    s.out_hdrs = [Wire(NetHdr()) for _ in xrange(num_ports)]
    hdr_nbits = s.in_hdrs[0].nbits
    msg_nbits = payload_nbits

    for i in xrange(num_ports):
      s.connect_pairs( 
        s.in_[i].msg.dest,     s.in_hdrs[i].dest,
        s.in_[i].msg.src,      s.in_hdrs[i].src,
        s.in_[i].msg.opaque,   s.in_hdrs[i].opaque,
        s.out_hdrs[i].dest,    s.out[i].msg.dest,
        s.out_hdrs[i].src,     s.out[i].msg.src,
        s.out_hdrs[i].opaque,  s.out[i].msg.opaque,
      )

      s.connect_pairs( 
        s.in_[i].val,         s.inner.in_val [i],
        s.in_[i].rdy,         s.inner.in_rdy [i],
        s.in_hdrs[i],         s.inner.in_msg_hdr     [ i*hdr_nbits : (i+1)*hdr_nbits ],
        s.in_[i].msg.payload, s.inner.in_msg_payload [ i*msg_nbits : (i+1)*msg_nbits ],
        s.out[i].val,         s.inner.out_val[i],
        s.out[i].rdy,         s.inner.out_rdy[i],
        s.out_hdrs[i],        s.inner.out_msg_hdr    [ i*hdr_nbits : (i+1)*hdr_nbits ],
        s.out[i].msg.payload, s.inner.out_msg_payload[ i*msg_nbits : (i+1)*msg_nbits ],
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
  from BusNetPRTL import BusNetPRTL as BusNetRTL
elif rtl_language == 'verilog':
  BusNetRTL = BusNetVRTL
else:
  raise Exception("Invalid RTL language!")
