//=========================================================================
// Router for ring network
//=========================================================================

`ifndef LAB4_NET_ROUTER_V
`define LAB4_NET_ROUTER_V

`include "vc/net-msgs.v"
`include "lab4_net/RouterDpathVRTL.v"
`include "lab4_net/RouterCtrlVRTL.v"

module lab4_net_RouterVRTL
#(
  parameter p_payload_nbits = 32
)
(
  input  logic                           clk,
  input  logic                           reset,

  input  logic     [1:0]                 router_id,

  input  net_hdr_t                       in0_msg_hdr,
  input  logic     [p_payload_nbits-1:0] in0_msg_payload,
  input  logic                           in0_val,
  output logic                           in0_rdy,

  output net_hdr_t                       out0_msg_hdr,
  output logic     [p_payload_nbits-1:0] out0_msg_payload,
  output logic                           out0_val,
  input  logic                           out0_rdy,

  input  net_hdr_t                       in1_msg_hdr,
  input  logic     [p_payload_nbits-1:0] in1_msg_payload,
  input  logic                           in1_val,
  output logic                           in1_rdy,

  output net_hdr_t                       out1_msg_hdr,
  output logic     [p_payload_nbits-1:0] out1_msg_payload,
  output logic                           out1_val,
  input  logic                           out1_rdy,

  input  net_hdr_t                       in2_msg_hdr,
  input  logic     [p_payload_nbits-1:0] in2_msg_payload,
  input  logic                           in2_val,
  output logic                           in2_rdy,

  output net_hdr_t                       out2_msg_hdr,
  output logic     [p_payload_nbits-1:0] out2_msg_payload,
  output logic                           out2_val,
  input  logic                           out2_rdy
);

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define wires
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  localparam c_nports = 4;
  localparam c_nports_width = $clog2(c_nports);

  logic [1:0] sel0;
  logic [1:0] sel1;
  logic [1:0] sel2;

  logic inq0_val;
  logic inq1_val;
  logic inq2_val;

  logic inq0_rdy;
  logic inq1_rdy;
  logic inq2_rdy;

  logic [c_nports_width-1:0] inq0_dest;
  logic [c_nports_width-1:0] inq1_dest;
  logic [c_nports_width-1:0] inq2_dest;

  lab4_net_RouterDpathVRTL
  #(
    .p_payload_nbits(p_payload_nbits)
  )
  dpath
  (
    .clk              (clk),
    .reset            (reset),

    .in0_val          (in0_val),
    .in0_rdy          (in0_rdy),
    .in0_msg_hdr      (in0_msg_hdr),
    .in0_msg_payload  (in0_msg_payload),

    .in1_val          (in1_val),
    .in1_rdy          (in1_rdy),
    .in1_msg_hdr      (in1_msg_hdr),
    .in1_msg_payload  (in1_msg_payload),

    .in2_val          (in2_val),
    .in2_rdy          (in2_rdy),
    .in2_msg_hdr      (in2_msg_hdr),
    .in2_msg_payload  (in2_msg_payload),

    .out0_msg_hdr     (out0_msg_hdr),
    .out0_msg_payload (out0_msg_payload),
    .out1_msg_hdr     (out1_msg_hdr),
    .out1_msg_payload (out1_msg_payload),
    .out2_msg_hdr     (out2_msg_hdr),
    .out2_msg_payload (out2_msg_payload),

    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    // LAB TASK: Connect datapath
    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    .sel0(sel0),
    .sel1(sel1),
    .sel2(sel2),

    .inq0_val(inq0_val),
    .inq1_val(inq1_val),
    .inq2_val(inq2_val),

    .inq0_rdy(inq0_rdy),
    .inq1_rdy(inq1_rdy),
    .inq2_rdy(inq2_rdy),

    .inq0_dest(inq0_dest),
    .inq1_dest(inq1_dest),
    .inq2_dest(inq2_dest)
  );

  lab4_net_RouterCtrlVRTL ctrl
  (
    .clk              (clk),
    .reset            (reset),

    .router_id        (router_id),

    .out0_val         (out0_val),
    .out0_rdy         (out0_rdy),

    .out1_val         (out1_val),
    .out1_rdy         (out1_rdy),

    .out2_val         (out2_val),
    .out2_rdy         (out2_rdy),

    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    // LAB TASK: Connect control unit
    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    .sel0(sel0),
    .sel1(sel1),
    .sel2(sel2),

    .inq0_val(inq0_val),
    .inq1_val(inq1_val),
    .inq2_val(inq2_val),

    .inq0_rdy(inq0_rdy),
    .inq1_rdy(inq1_rdy),
    .inq2_rdy(inq2_rdy),

    .inq0_dest(inq0_dest),
    .inq1_dest(inq1_dest),
    .inq2_dest(inq2_dest)
  );

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------
  vc_NetHdrTrace in0_hdr_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (in0_val),
    .rdy   (in0_rdy),
    .hdr   (in0_msg_hdr)
  );

  vc_NetHdrTrace in1_hdr_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (in1_val),
    .rdy   (in1_rdy),
    .hdr   (in1_msg_hdr)
  );

  vc_NetHdrTrace in2_hdr_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (in2_val),
    .rdy   (in2_rdy),
    .hdr   (in2_msg_hdr)
  );

  vc_NetHdrTrace out0_hdr_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (out0_val),
    .rdy   (out0_rdy),
    .hdr   (out0_msg_hdr)
  );

  vc_NetHdrTrace out1_hdr_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (out1_val),
    .rdy   (out1_rdy),
    .hdr   (out1_msg_hdr)
  );

  vc_NetHdrTrace out2_hdr_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (out2_val),
    .rdy   (out2_rdy),
    .hdr   (out2_msg_hdr)
  );

  logic [6*8-1:0] in0_str;
  logic [6*8-1:0] in1_str;
  logic [6*8-1:0] in2_str;

  `VC_TRACE_BEGIN
  begin
    $sformat( in0_str, "%x:%x>%x", in0_msg_hdr.opaque, in0_msg_hdr.src, in0_msg_hdr.dest );
    $sformat( in1_str, "%x:%x>%x", in1_msg_hdr.opaque, in1_msg_hdr.src, in1_msg_hdr.dest );
    $sformat( in2_str, "%x:%x>%x", in2_msg_hdr.opaque, in2_msg_hdr.src, in2_msg_hdr.dest );
    vc_trace.append_str( trace_str, "(" );
    vc_trace.append_val_rdy_str( trace_str, in0_val, in0_rdy, {{4048{1'b0}}, in0_str} );
    vc_trace.append_str( trace_str, "|" );
    vc_trace.append_val_rdy_str( trace_str, in1_val, in1_rdy, {{4048{1'b0}}, in1_str} );
    vc_trace.append_str( trace_str, "|" );
    vc_trace.append_val_rdy_str( trace_str, in2_val, in2_rdy, {{4048{1'b0}}, in2_str} );
    vc_trace.append_str( trace_str, ")" );
  end
  `VC_TRACE_END

endmodule

`endif /* LAB4_NET_ROUTER_V */
