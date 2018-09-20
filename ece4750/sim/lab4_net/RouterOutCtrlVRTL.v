//=========================================================================
// Router Control Unit
//=========================================================================

`ifndef LAB4_NET_ROUTER_OUT_CTRL_V
`define LAB4_NET_ROUTER_OUT_CTRL_V

`include "vc/arbiters.v"

module lab4_net_RouterOutCtrlVRTL
(
  input  logic       clk,
  input  logic       reset,

  output logic       out_val,
  input  logic       out_rdy,

  output logic [1:0] sel,

  input  logic [2:0] in_reqs,

  output logic       in0_rdy,
  output logic       in1_rdy,
  output logic       in2_rdy
);

  localparam num_interfaces = 3;

  logic [2:0]      grants;
  logic            arbiter_en;

  // input queue ready flags are set if they were read by the
  // arbiter (granted path) and that arbiter was enabled (value
  // was read out).
  assign in0_rdy = arbiter_en && grants[0];
  assign in1_rdy = arbiter_en && grants[1];
  assign in2_rdy = arbiter_en && grants[2];

  // select = encoding of grants
  assign sel =
    (grants[2] == 1) ? 2'd2 :
    (grants[1] == 1) ? 2'd1 :
    (grants[0] == 1) ? 2'd0 : 2'b0;

  // Output is valid if a request was successfully arbitrated
  assign out_val = grants != {num_interfaces{1'b0}};

  // Only move arbiter when current value was valid and read out
  assign arbiter_en = out_val && out_rdy;

  vc_RoundRobinArbEn #( num_interfaces ) arbiter
  (
    .clk(clk),
    .reset(reset),
    .en(arbiter_en),
    .reqs(in_reqs),
    .grants(grants)
  );

endmodule

`endif /* LAB4_NET_ROUTER_OUT_CTRL_V */
