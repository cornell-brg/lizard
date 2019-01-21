//-----------------------------------------------------------------------------
// WrapInc_0x1e78bd01b0125419
//-----------------------------------------------------------------------------
// nbits: 2
// size: 4
// up: True
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module WrapInc_0x1e78bd01b0125419
(
  input  wire [   0:0] clk,
  input  wire [   1:0] inc_in_,
  output reg  [   1:0] inc_out,
  input  wire [   0:0] reset
);

  // localparam declarations
  localparam size = 4;



  // PYMTL SOURCE:
  //
  // @s.combinational
  // def compute():
  //         if s.inc.in_ == size - 1:
  //           s.inc.out.v = 0
  //         else:
  //           s.inc.out.v = s.inc.in_ + 1

  // logic for compute()
  always @ (*) begin
    if ((inc_in_ == (size-1))) begin
      inc_out = 0;
    end
    else begin
      inc_out = (inc_in_+1);
    end
  end


endmodule // WrapInc_0x1e78bd01b0125419
`default_nettype wire

