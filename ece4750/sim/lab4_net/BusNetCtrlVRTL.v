`ifndef LAB4_NET_BUS_NET_CTRL_V
`define LAB4_NET_BUS_NET_CTRL_V

`include "vc/arbiters.v"
`include "lab4_net/Coders.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab4_net_BusNetCtrlVRTL
(
  input  logic                                 clk,
  input  logic                                 reset,

  output logic [c_nports-1:0]                  out_val,
  input  logic [c_nports-1:0]                  out_rdy,

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define additional ports
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  input  logic [c_nports-1:0][1:0]             inq_dest,
  input  logic [c_nports-1:0]                  inq_val,
  output logic [c_nports-1:0]                  inq_rdy,

  output  logic [c_sel_width-1:0]               sel
);
  // c_nports included for convenience to avoid having magic numbers, but
  // your design does not need to support other values of c_nports.
  localparam c_nports = 4;
  localparam c_sel_width = $clog2(c_nports);

  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement control unit
  //'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  logic [c_nports-1:0]      grants;
  logic                     arbiter_en;

  lab4_net_OneHotEncoderVRTL #(c_nports) out_val_encoder (
    .one_hot(grants),
    .encoded(sel)
  );
  logic [c_nports-1:0] dest_hot;
  lab4_net_OneHotDecoderVRTL #(c_nports) out_val_decoder (
    .to_decode(inq_dest[sel]),
    .one_hot(dest_hot)
  );
  assign out_val = grants == {c_nports{1'b0}} ? {c_nports{1'b0}} : dest_hot;

  logic ready_helper [c_nports - 1:0];
  genvar i;
  generate
  for ( i = 0; i < c_nports; i = i + 1 ) begin: INQRDY

    assign inq_rdy[i] = arbiter_en && grants[i];
    assign ready_helper[i] = (out_val[i] && out_rdy[i]) || (i == 0 ? 1'b0 : ready_helper[i-1]);

  end
  endgenerate

  assign arbiter_en = ready_helper[c_nports - 1];

  vc_RoundRobinArbEn #(c_nports) arbiter
  (
    .clk(clk),
    .reset(reset),
    .en(arbiter_en),
    .reqs(inq_val),
    .grants(grants)
  );


endmodule

`endif /* LAB4_NET_BUS_NET_CTRL_V */
