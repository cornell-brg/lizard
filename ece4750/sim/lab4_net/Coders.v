`ifndef LAB4_NET_CODERS
`define LAB4_NET_CODERS

`include "vc/net-msgs.v"
`include "vc/queues.v"
`include "vc/buses.v"

module lab4_net_OneHotDecoderVRTL
#(
  parameter max_val = 32
)
(
  input logic [$clog2(max_val) - 1:0] to_decode,
  output logic [max_val - 1:0] one_hot
);

  genvar i;
  generate
  for ( i = 0; i < max_val; i = i + 1 ) begin: TEDDY_BEAR
      assign one_hot[i] = (i[$clog2(max_val) - 1:0] == to_decode);
  end
  endgenerate

endmodule


module lab4_net_OneHotEncoderVRTL
#(
  parameter max_val = 32
)
(
  input logic [max_val - 1:0] one_hot,
  output logic [$clog2(max_val) - 1:0] encoded
);

  logic valid;
  logic [$clog2(max_val) - 1:0] options[max_val - 1:0];

  assign options[{$clog2(max_val){1'b0}}] = {$clog2(max_val){1'b0}};

  genvar i;
  generate
  for ( i = 1; i < max_val; i = i + 1 ) begin: TEDDY_BEAR
      assign options[i] = one_hot[i] ? i[$clog2(max_val) - 1:0] : options[i-1];
  end
  endgenerate

  assign encoded = options[max_val - 1];

endmodule

`endif
