//========================================================================
// Verilog Components: Crossbars
//========================================================================

`ifndef VC_CROSSBARS_V
`define VC_CROSSBARS_V

`include "vc/muxes.v"

//------------------------------------------------------------------------
// 2 input, 2 output crossbar
//------------------------------------------------------------------------

module vc_Crossbar2
#(
  parameter p_nbits = 32
)
(
  input  logic [p_nbits-1:0]   in0,
  input  logic [p_nbits-1:0]   in1,

  input  logic                 sel0,
  input  logic                 sel1,

  output logic [p_nbits-1:0]   out0,
  output logic [p_nbits-1:0]   out1
);

  vc_Mux2#(p_nbits) out0_mux
  (
    .in0 (in0),
    .in1 (in1),
    .sel (sel0),
    .out (out0)
  );

  vc_Mux2#(p_nbits) out1_mux
  (
    .in0 (in0),
    .in1 (in1),
    .sel (sel1),
    .out (out1)
  );

endmodule

//------------------------------------------------------------------------
// 3 input, 3 output crossbar
//------------------------------------------------------------------------

module vc_Crossbar3
#(
  parameter p_nbits = 32
)
(
  input  logic [p_nbits-1:0]   in0,
  input  logic [p_nbits-1:0]   in1,
  input  logic [p_nbits-1:0]   in2,

  input  logic [1:0]           sel0,
  input  logic [1:0]           sel1,
  input  logic [1:0]           sel2,

  output logic [p_nbits-1:0]   out0,
  output logic [p_nbits-1:0]   out1,
  output logic [p_nbits-1:0]   out2
);

  vc_Mux3#(p_nbits) out0_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .sel (sel0),
    .out (out0)
  );

  vc_Mux3#(p_nbits) out1_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .sel (sel1),
    .out (out1)
  );

  vc_Mux3#(p_nbits) out2_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .sel (sel2),
    .out (out2)
  );

endmodule

//------------------------------------------------------------------------
// 4 input, 4 output crossbar
//------------------------------------------------------------------------

module vc_Crossbar4
#(
  parameter p_nbits = 32
)
(
  input  logic [p_nbits-1:0]   in0,
  input  logic [p_nbits-1:0]   in1,
  input  logic [p_nbits-1:0]   in2,
  input  logic [p_nbits-1:0]   in3,

  input  logic [1:0]           sel0,
  input  logic [1:0]           sel1,
  input  logic [1:0]           sel2,
  input  logic [1:0]           sel3,

  output logic [p_nbits-1:0]   out0,
  output logic [p_nbits-1:0]   out1,
  output logic [p_nbits-1:0]   out2,
  output logic [p_nbits-1:0]   out3
);

  vc_Mux4#(p_nbits) out0_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .in3 (in3),
    .sel (sel0),
    .out (out0)
  );

  vc_Mux4#(p_nbits) out1_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .in3 (in3),
    .sel (sel1),
    .out (out1)
  );

  vc_Mux4#(p_nbits) out2_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .in3 (in3),
    .sel (sel2),
    .out (out2)
  );

  vc_Mux4#(p_nbits) out3_mux
  (
    .in0 (in0),
    .in1 (in1),
    .in2 (in2),
    .in3 (in3),
    .sel (sel3),
    .out (out3)
  );

endmodule

`endif /* VC_CROSSBARS_V */
