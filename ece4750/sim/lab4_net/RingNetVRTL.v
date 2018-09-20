//=========================================================================
// Ring-based network
//=========================================================================

`ifndef LAB4_NET_RING_NET_V
`define LAB4_NET_RING_NET_V

`include "vc/net-msgs.v"
`include "lab4_net/RouterVRTL.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

// Helper macros to calculate `PREVious and `NEXT router ids

`define PREV(i_) ( ( i_ + c_nports - 1 ) % c_nports )
`define NEXT(i_) ( ( i_ + 1 ) % c_nports )

module lab4_net_RingNetVRTL
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
  localparam c_nports_width = $clog2(c_nports);

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Compose ring network
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  net_hdr_t                       in0_msg_hdr    [c_nports-1:0];
  logic     [p_payload_nbits-1:0] in0_msg_payload[c_nports-1:0];
  logic                           in0_val        [c_nports-1:0];
  logic                           in0_rdy        [c_nports-1:0];

  net_hdr_t                       in2_msg_hdr    [c_nports-1:0];
  logic     [p_payload_nbits-1:0] in2_msg_payload[c_nports-1:0];
  logic                           in2_val        [c_nports-1:0];
  logic                           in2_rdy        [c_nports-1:0];

  genvar i;
  generate
  for (i = 0; i < c_nports; i = i + 1) begin: ROUTER
    lab4_net_RouterVRTL #(p_payload_nbits) router (
      .clk              (clk),
      .reset            (reset),
      .router_id        (i[c_nports_width - 1:0]),

      .in0_msg_hdr      (in0_msg_hdr     [i]),
      .in0_msg_payload  (in0_msg_payload [i]),
      .in0_val          (in0_val         [i]),
      .in0_rdy          (in0_rdy         [i]),

      .in1_msg_hdr      (in_msg_hdr      [i]),
      .in1_msg_payload  (in_msg_payload  [i]),
      .in1_val          (in_val          [i]),
      .in1_rdy          (in_rdy          [i]),

      .in2_msg_hdr      (in2_msg_hdr     [i]),
      .in2_msg_payload  (in2_msg_payload [i]),
      .in2_val          (in2_val         [i]),
      .in2_rdy          (in2_rdy         [i]),

      .out0_msg_hdr      (in2_msg_hdr    [`PREV(i)]),
      .out0_msg_payload  (in2_msg_payload[`PREV(i)]),
      .out0_val          (in2_val        [`PREV(i)]),
      .out0_rdy          (in2_rdy        [`PREV(i)]),

      .out1_msg_hdr      (out_msg_hdr    [i]),
      .out1_msg_payload  (out_msg_payload[i]),
      .out1_val          (out_val        [i]),
      .out1_rdy          (out_rdy        [i]),

      .out2_msg_hdr      (in0_msg_hdr    [`NEXT(i)]),
      .out2_msg_payload  (in0_msg_payload[`NEXT(i)]),
      .out2_val          (in0_val        [`NEXT(i)]),
      .out2_rdy          (in0_rdy        [`NEXT(i)])
    );
  end
  endgenerate



  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------
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
    ROUTER[0].router.line_trace( trace_str );
    ROUTER[1].router.line_trace( trace_str );
    ROUTER[2].router.line_trace( trace_str );
    ROUTER[3].router.line_trace( trace_str );
  end
  `VC_TRACE_END

endmodule

`endif /* LAB4_NET_RING_NET_V */
