//=========================================================================
// Router Control Unit
//=========================================================================

`ifndef LAB4_NET_ROUTER_CTRL_V
`define LAB4_NET_ROUTER_CTRL_V

`include "vc/net-msgs.v"
`include "vc/arbiters.v"
`include "lab4_net/RouterOutCtrlVRTL.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab4_net_RouterCtrlVRTL
(
  input  logic       clk,
  input  logic       reset,

  input  logic [1:0] router_id,

  output logic       out0_val,
  input  logic       out0_rdy,

  output logic       out1_val,
  input  logic       out1_rdy,

  output logic       out2_val,
  input  logic       out2_rdy,

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define additional ports
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  output logic [1:0] sel0,
  output logic [1:0] sel1,
  output logic [1:0] sel2,

  input  logic inq0_val,
  input  logic inq1_val,
  input  logic inq2_val,

  output logic inq0_rdy,
  output logic inq1_rdy,
  output logic inq2_rdy,

  input  logic [c_nports_width-1:0] inq0_dest,
  input  logic [c_nports_width-1:0] inq1_dest,
  input  logic [c_nports_width-1:0] inq2_dest
);

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement control unit
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  localparam c_nports = 4;
  localparam c_nports_width = $clog2(c_nports);
  localparam num_interfaces = 3;

  logic [num_interfaces-1:0]      in0_reqs;
  logic [num_interfaces-1:0]      in1_reqs;
  logic [num_interfaces-1:0]      in2_reqs;

  logic [num_interfaces-1:0]      in0_rdys;
  logic [num_interfaces-1:0]      in1_rdys;
  logic [num_interfaces-1:0]      in2_rdys;

  assign inq0_rdy = (in0_rdys != {num_interfaces{1'b0}});
  assign inq1_rdy = (in1_rdys != {num_interfaces{1'b0}});
  assign inq2_rdy = (in2_rdys != {num_interfaces{1'b0}});

  logic [c_nports_width-1:0] left;
  logic [c_nports_width-1:0] right;

  logic in1_out0;
  logic in1_out2;

  assign right = inq1_dest - router_id;
  assign left = router_id - inq1_dest;

  // if the input terminal should go left
  assign in1_out0 =
    (left < right)  ? 1'b1 :
    (left == right) ?
      ((inq1_dest[1'b0]) ? 1'b1 : 1'b0) :
      1'b0;

  // if the input terminal should go right
  assign in1_out2 =
    (right < left) ? 1'b1 :
    (left == right) ?
      ((~inq1_dest[1'b0]) ? 1'b1 : 1'b0) :
      1'b0 ;

  // input requests for output 0 arbiter are based on:
  // input being valid and this not being the packets destination
  // and in1 wanting to go left
  assign in0_reqs = {
    (inq2_val && (inq2_dest != router_id)) ? 1'b1 : 1'b0,
    (inq1_val && in1_out0 && (inq1_dest != router_id)) ? 1'b1 : 1'b0,
    1'b0 // input 0 will never go backward
  };

  // input requests for output 1 arbiter are based on:
  // input being valid and this being the packets destination
  assign in1_reqs = {
    inq2_val && (inq2_dest == router_id),
    inq1_val && (inq1_dest == router_id),
    inq0_val && (inq0_dest == router_id)
  };

  // input requests for output 2 arbiter are based on:
  // input being valid and this not being the packets destination
  // and in1 wanting to go right
  assign in2_reqs = {
    1'b0, // input 2 will never go backward
    (inq1_val && in1_out2 && (inq1_dest != router_id)) ? 1'b1 : 1'b0,
    (inq0_val && (inq0_dest != router_id)) ? 1'b1 : 1'b0
  };

  lab4_net_RouterOutCtrlVRTL out0_arbiter
  (
    .clk(clk),
    .reset(reset),

    .out_val(out0_val),
    .out_rdy(out0_rdy),
    .sel(sel0),
    .in_reqs(in0_reqs),
    .in0_rdy(in0_rdys[0]),
    .in1_rdy(in1_rdys[0]),
    .in2_rdy(in2_rdys[0])
  );

  lab4_net_RouterOutCtrlVRTL out1_arbiter
  (
    .clk(clk),
    .reset(reset),

    .out_val(out1_val),
    .out_rdy(out1_rdy),
    .sel(sel1),
    .in_reqs(in1_reqs),
    .in0_rdy(in0_rdys[1]),
    .in1_rdy(in1_rdys[1]),
    .in2_rdy(in2_rdys[1])
  );

  lab4_net_RouterOutCtrlVRTL out2_arbiter
  (
    .clk(clk),
    .reset(reset),

    .out_val(out2_val),
    .out_rdy(out2_rdy),
    .sel(sel2),
    .in_reqs(in2_reqs),
    .in0_rdy(in0_rdys[2]),
    .in1_rdy(in1_rdys[2]),
    .in2_rdy(in2_rdys[2])
  );

endmodule

`endif /* LAB4_NET_ROUTER_CTRL_V */
