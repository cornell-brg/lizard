//-----------------------------------------------------------------------------
// WrapIncVar_0x5d39f8009fda7e2
//-----------------------------------------------------------------------------
// nbits: 2
// size: 4
// up: True
// max_ops: 2
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module WrapIncVar_0x5d39f8009fda7e2
(
  input  wire [   0:0] clk,
  input  wire [   1:0] inc_in_,
  input  wire [   1:0] inc_ops,
  output reg  [   1:0] inc_out,
  input  wire [   0:0] reset
);

  // wire declarations
  wire   [   1:0] workaround_units_inc_out$000;
  wire   [   1:0] workaround_units_inc_out$001;


  // units$000 temporaries
  wire   [   0:0] units$000$reset;
  wire   [   0:0] units$000$clk;
  wire   [   1:0] units$000$inc_in_;
  wire   [   1:0] units$000$inc_out;

  WrapInc_0x1e78bd01b0125419 units$000
  (
    .reset   ( units$000$reset ),
    .clk     ( units$000$clk ),
    .inc_in_ ( units$000$inc_in_ ),
    .inc_out ( units$000$inc_out )
  );

  // units$001 temporaries
  wire   [   0:0] units$001$reset;
  wire   [   0:0] units$001$clk;
  wire   [   1:0] units$001$inc_in_;
  wire   [   1:0] units$001$inc_out;

  WrapInc_0x1e78bd01b0125419 units$001
  (
    .reset   ( units$001$reset ),
    .clk     ( units$001$clk ),
    .inc_in_ ( units$001$inc_in_ ),
    .inc_out ( units$001$inc_out )
  );

  // signal connections
  assign units$000$clk                = clk;
  assign units$000$inc_in_            = inc_in_;
  assign units$000$reset              = reset;
  assign units$001$clk                = clk;
  assign units$001$inc_in_            = units$000$inc_out;
  assign units$001$reset              = reset;
  assign workaround_units_inc_out$000 = units$000$inc_out;
  assign workaround_units_inc_out$001 = units$001$inc_out;

  // array declarations
  wire   [   1:0] workaround_units_inc_out[0:1];
  assign workaround_units_inc_out[  0] = workaround_units_inc_out$000;
  assign workaround_units_inc_out[  1] = workaround_units_inc_out$001;

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def compute():
  //       if s.inc.ops == 0:
  //         s.inc.out.v = s.inc.in_
  //       else:
  //         s.inc.out.v = s.workaround_units_inc_out[ s.inc.ops - 1 ]

  // logic for compute()
  always @ (*) begin
    if ((inc_ops == 0)) begin
      inc_out = inc_in_;
    end
    else begin
      inc_out = workaround_units_inc_out[(inc_ops-1)];
    end
  end


endmodule // WrapIncVar_0x5d39f8009fda7e2
`default_nettype wire

//-----------------------------------------------------------------------------
// WrapInc_0x1e78bd01b0125419
//-----------------------------------------------------------------------------
// nbits: 2
// size: 4
// up: True
// dump-vcd: False
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

