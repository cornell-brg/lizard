
//=========================================================================
// Integer Multiplier Shift Counter
//=========================================================================

`ifndef LAB1_IMUL_INT_MUL_SFT_CTR_V
`define LAB1_IMUL_INT_MUL_SFT_CTR_V

`include "vc/trace.v"

//=========================================================================
// Integer Multiplier Shift Counter Implementation
//=========================================================================

module lab1_imul_IntMulSftCtrVRT
(
  input  logic [31:0] val,
  output logic [4:0] sft 
);

  always_comb begin
    if (val == 32'b0 || val == 32'b1) sft = 5'd0;
    else if (val[1] == 1'b1) sft = 5'd1;
    else if (val[2] == 1'b1) sft = 5'd2;
    else if (val[3] == 1'b1) sft = 5'd3;
    else if (val[4] == 1'b1) sft = 5'd4;
    else if (val[5] == 1'b1) sft = 5'd5;
    else sft = 5'd6;
  end 

endmodule

`endif /* LAB1_IMUL_INT_MUL_SFT_CTR_V */

