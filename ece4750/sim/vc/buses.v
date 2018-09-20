`ifndef VC_BUSES_V
`define VC_BUSES_V

module vc_Bus
#(
  parameter p_width = 32,
  parameter p_num_ports = 4
)
(
  input  logic [c_sel_width-1:0]              sel,
  input  logic [p_num_ports-1:0][p_width-1:0] in_,
  output logic [p_num_ports-1:0][p_width-1:0] out
);
  localparam c_sel_width = $clog2(p_num_ports);

  genvar i;
  generate
  for (i = 0; i < p_num_ports; i = i + 1) begin: OUT_PORTS
    assign out[i] = in_[sel];
  end
  endgenerate

endmodule


`endif /* VC_BUSES_V */
