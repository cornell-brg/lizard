//=========================================================================
// Router datapath
//=========================================================================

`ifndef LAB4_NET_ROUTER_DPATH_V
`define LAB4_NET_ROUTER_DPATH_V

`include "vc/net-msgs.v"
`include "vc/queues.v"
`include "vc/crossbars.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab4_net_RouterDpathVRTL
#(
  parameter p_payload_nbits = 32
)
(
  input  logic                           clk,
  input  logic                           reset,

  input  net_hdr_t                       in0_msg_hdr,
  input  logic     [p_payload_nbits-1:0] in0_msg_payload,
  input  logic                           in0_val,
  output logic                           in0_rdy,

  input  net_hdr_t                       in1_msg_hdr,
  input  logic     [p_payload_nbits-1:0] in1_msg_payload,
  input  logic                           in1_val,
  output logic                           in1_rdy,

  input  net_hdr_t                       in2_msg_hdr,
  input  logic     [p_payload_nbits-1:0] in2_msg_payload,
  input  logic                           in2_val,
  output logic                           in2_rdy,

  output net_hdr_t                       out0_msg_hdr,
  output logic     [p_payload_nbits-1:0] out0_msg_payload,

  output net_hdr_t                       out1_msg_hdr,
  output logic     [p_payload_nbits-1:0] out1_msg_payload,

  output net_hdr_t                       out2_msg_hdr,
  output logic     [p_payload_nbits-1:0] out2_msg_payload,

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define additional ports
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  input  logic [1:0] sel0,
  input  logic [1:0] sel1,
  input  logic [1:0] sel2,

  output logic inq0_val,
  output logic inq1_val,
  output logic inq2_val,

  input  logic inq0_rdy,
  input  logic inq1_rdy,
  input  logic inq2_rdy,

  output logic [c_nports_width-1:0] inq0_dest,
  output logic [c_nports_width-1:0] inq1_dest,
  output logic [c_nports_width-1:0] inq2_dest
);

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement datapath
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  localparam c_nports = 4;
  localparam c_nports_width = $clog2(c_nports);
  localparam num_entries = 2;
  localparam hdr_width = $bits(net_hdr_t);
  localparam msg_width = hdr_width + p_payload_nbits;

  logic [msg_width-1:0] inq0_msg;
  logic [msg_width-1:0] inq1_msg;
  logic [msg_width-1:0] inq2_msg;

  net_hdr_t inq0_hdr;
  net_hdr_t inq1_hdr;
  net_hdr_t inq2_hdr;

  logic [msg_width-1:0] out0_msg;
  logic [msg_width-1:0] out1_msg;
  logic [msg_width-1:0] out2_msg;

  // assign inq1_val = in1_val;
  // assign in1_rdy = inq1_rdy;
  // assign inq1_msg = {in1_msg_hdr, in1_msg_payload};

  assign inq0_hdr = inq0_msg[msg_width-1:p_payload_nbits];
  assign inq1_hdr = inq1_msg[msg_width-1:p_payload_nbits];
  assign inq2_hdr = inq2_msg[msg_width-1:p_payload_nbits];

  assign inq0_dest = inq0_hdr.dest;
  assign inq1_dest = inq1_hdr.dest;
  assign inq2_dest = inq2_hdr.dest;

  assign out0_msg_hdr = out0_msg[msg_width-1:p_payload_nbits];
  assign out1_msg_hdr = out1_msg[msg_width-1:p_payload_nbits];
  assign out2_msg_hdr = out2_msg[msg_width-1:p_payload_nbits];

  assign out0_msg_payload = out0_msg[p_payload_nbits-1:0];
  assign out1_msg_payload = out1_msg[p_payload_nbits-1:0];
  assign out2_msg_payload = out2_msg[p_payload_nbits-1:0];

  vc_Queue #(
    `VC_QUEUE_NORMAL,
    msg_width,
    num_entries
  )
  in0_queue
  (
    .clk(clk),
    .reset(reset),

    .enq_val(in0_val),
    .enq_rdy(in0_rdy),
    .enq_msg({
      in0_msg_hdr,
      in0_msg_payload
      }),

    .deq_val(inq0_val),
    .deq_rdy(inq0_rdy),
    .deq_msg(inq0_msg),
  );

  vc_Queue #(
    `VC_QUEUE_NORMAL,
    msg_width,
    num_entries
  )
  in1_queue
  (
    .clk(clk),
    .reset(reset),

    .enq_val(in1_val),
    .enq_rdy(in1_rdy),
    .enq_msg({
      in1_msg_hdr,
      in1_msg_payload
      }),

    .deq_val(inq1_val),
    .deq_rdy(inq1_rdy),
    .deq_msg(inq1_msg),
  );

  vc_Queue #(
    `VC_QUEUE_NORMAL,
    msg_width,
    num_entries
  )
  in2_queue
  (
    .clk(clk),
    .reset(reset),

    .enq_val(in2_val),
    .enq_rdy(in2_rdy),
    .enq_msg({
      in2_msg_hdr,
      in2_msg_payload
      }),

    .deq_val(inq2_val),
    .deq_rdy(inq2_rdy),
    .deq_msg(inq2_msg),
  );

  vc_Crossbar3 #( msg_width ) crossbar
  (
    .in0(inq0_msg),
    .in1(inq1_msg),
    .in2(inq2_msg),
    .sel0(sel0),
    .sel1(sel1),
    .sel2(sel2),
    .out0(out0_msg),
    .out1(out1_msg),
    .out2(out2_msg)
  );

endmodule

`endif /* LAB4_NET_ROUTER_DPATH_V */
