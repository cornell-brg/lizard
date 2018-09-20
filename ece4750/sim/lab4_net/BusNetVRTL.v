//=========================================================================
// Bus-based network
//=========================================================================

`ifndef LAB4_NET_BUS_NET_V
`define LAB4_NET_BUS_NET_V

`include "vc/net-msgs.v"
`include "lab4_net/BusNetCtrlVRTL.v"
`include "lab4_net/BusNetDpathVRTL.v"

module lab4_net_BusNetVRTL
#(
  parameter p_payload_nbits = 32
)
(
  input logic clk,
  input logic reset,

  input  net_hdr_t [c_nports-1:0]                      in_msg_hdr,
  input  logic     [c_nports-1:0][p_payload_nbits-1:0] in_msg_payload,
  input  logic     [c_nports-1:0]                      in_val,
  output logic     [c_nports-1:0]                      in_rdy,

  output net_hdr_t [c_nports-1:0]                      out_msg_hdr,
  output logic     [c_nports-1:0][p_payload_nbits-1:0] out_msg_payload,
  output logic     [c_nports-1:0]                      out_val,
  input  logic     [c_nports-1:0]                      out_rdy
);
  // c_nports included for convenience to avoid having magic numbers, but 
  // your design does not need to support other values of c_nports.
  localparam c_nports = 4;
  localparam c_sel_width = $clog2(c_nports);

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define wires
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  logic     [c_nports-1:0][1:0]                 inq_dest;
  logic     [c_nports-1:0]                      inq_val;
  logic     [c_nports-1:0]                      inq_rdy;

  logic      [c_sel_width-1:0]                  sel;

  lab4_net_BusNetCtrlVRTL ctrl
  (
    .clk      (clk),
    .reset    (reset),

    .out_val  (out_val),
    .out_rdy  (out_rdy),

    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    // LAB TASK: Connect control unit
    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    .inq_dest(inq_dest),
    .inq_val(inq_val),
    .inq_rdy(inq_rdy),
    .sel(sel)
  );

  lab4_net_BusNetDpathVRTL #(p_payload_nbits) dpath
  (
    .clk             (clk),
    .reset           (reset),

    .in_val          (in_val),
    .in_rdy          (in_rdy),
    .in_msg_hdr      (in_msg_hdr),
    .in_msg_payload  (in_msg_payload),

    .out_msg_hdr     (out_msg_hdr),
    .out_msg_payload (out_msg_payload),

    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    // LAB TASK: Connect datapath
    //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    .inq_dest(inq_dest),
    .inq_val(inq_val),
    .inq_rdy(inq_rdy),
    .sel(sel)
  );

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------
  genvar i;
  generate
  for (i = 0; i < c_nports; i = i + 1) begin: HEADER
    vc_NetHdrTrace in_hdr_trace
    (
      .clk   (clk),
      .reset (reset),
      .val   (in_val[i]),
      .rdy   (in_rdy[i]),
      .hdr   (in_msg_hdr[i])
    );

    vc_NetHdrTrace out_hdr_trace
    (
      .clk   (clk),
      .reset (reset),
      .val   (out_val[i]),
      .rdy   (out_rdy[i]),
      .hdr   (out_msg_hdr[i])
    );
  end
  endgenerate

  logic [6*8-1:0] in_str;
  logic [6*8-1:0] out_str;

  `VC_TRACE_BEGIN
  begin
    for (integer i = 0; i < c_nports; i = i + 1) begin
      $sformat( in_str, "%x:%x>%x", in_msg_hdr[i].opaque, in_msg_hdr[i].src, in_msg_hdr[i].dest );
      $sformat( out_str, "%x:%x>%x", out_msg_hdr[i].opaque, out_msg_hdr[i].src, out_msg_hdr[i].dest );
      vc_trace.append_str( trace_str, "(" );
      vc_trace.append_val_rdy_str( trace_str, in_val[i], in_rdy[i], {{4048{1'b0}}, in_str} );
      vc_trace.append_str( trace_str, "|" );
      vc_trace.append_val_rdy_str( trace_str, out_val[i], out_rdy[i], {{4048{1'b0}}, out_str} );
      vc_trace.append_str( trace_str, ")" );
    end
  end
  `VC_TRACE_END

endmodule

`endif /* LAB4_NET_BUS_NET_V */
