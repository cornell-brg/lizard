//-----------------------------------------------------------------------------
// WrapInc_0x418d9f90d853f7a2
//-----------------------------------------------------------------------------
// nbits: 2
// size: 4
// up: False
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module WrapInc_0x418d9f90d853f7a2
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
  //         if s.inc.in_ == 0:
  //           s.inc.out.v = size - 1
  //         else:
  //           s.inc.out.v = s.inc.in_ - 1

  // logic for compute()
  always @ (*) begin
    if ((inc_in_ == 0)) begin
      inc_out = (size-1);
    end
    else begin
      inc_out = (inc_in_-1);
    end
  end


endmodule // WrapInc_0x418d9f90d853f7a2
`default_nettype wire

