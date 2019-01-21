//-----------------------------------------------------------------------------
// RingBuffer_0x64da68b78203a525
//-----------------------------------------------------------------------------
// NUM_ENTRIES: 4
// ENTRY_BITWIDTH: 16
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module RingBuffer_0x64da68b78203a525
(
  input  wire [   0:0] alloc_port_call,
  output reg  [   1:0] alloc_port_index,
  output reg  [   0:0] alloc_port_rdy,
  input  wire [  15:0] alloc_port_value,
  input  wire [   0:0] clk,
  input  wire [   0:0] peek_port_call,
  output reg  [   0:0] peek_port_rdy,
  output reg  [  15:0] peek_port_value,
  input  wire [   0:0] remove_port_call,
  output reg  [   0:0] remove_port_rdy,
  input  wire [   0:0] reset,
  input  wire [   0:0] update_port_call,
  input  wire [   1:0] update_port_index,
  output reg  [   0:0] update_port_rdy,
  input  wire [  15:0] update_port_value
);

  // register declarations
  reg    [   0:0] empty;
  reg    [   1:0] head$in_;
  reg    [   1:0] next_slot;
  reg    [   2:0] num$in_;
  reg    [   2:0] num_next;

  // localparam declarations
  localparam IDX_NBITS = 2;
  localparam NUM_ENTRIES = 4;

  // loop variable declarations
  integer i;

  // num temporaries
  wire   [   0:0] num$reset;
  wire   [   0:0] num$clk;
  wire   [   2:0] num$out;

  RegRst_0x1099485158c4776f num
  (
    .reset ( num$reset ),
    .in_   ( num$in_ ),
    .clk   ( num$clk ),
    .out   ( num$out )
  );

  // head temporaries
  wire   [   0:0] head$reset;
  wire   [   0:0] head$clk;
  wire   [   1:0] head$out;

  RegRst_0x9f365fdf6c8998a head
  (
    .reset ( head$reset ),
    .in_   ( head$in_ ),
    .clk   ( head$clk ),
    .out   ( head$out )
  );

  // data$000 temporaries
  wire   [   0:0] data$000$reset;
  wire   [  15:0] data$000$in_;
  wire   [   0:0] data$000$clk;
  wire   [   0:0] data$000$en;
  wire   [  15:0] data$000$out;

  RegEn_0x68db79c4ec1d6e5b data$000
  (
    .reset ( data$000$reset ),
    .in_   ( data$000$in_ ),
    .clk   ( data$000$clk ),
    .en    ( data$000$en ),
    .out   ( data$000$out )
  );

  // data$001 temporaries
  wire   [   0:0] data$001$reset;
  wire   [  15:0] data$001$in_;
  wire   [   0:0] data$001$clk;
  wire   [   0:0] data$001$en;
  wire   [  15:0] data$001$out;

  RegEn_0x68db79c4ec1d6e5b data$001
  (
    .reset ( data$001$reset ),
    .in_   ( data$001$in_ ),
    .clk   ( data$001$clk ),
    .en    ( data$001$en ),
    .out   ( data$001$out )
  );

  // data$002 temporaries
  wire   [   0:0] data$002$reset;
  wire   [  15:0] data$002$in_;
  wire   [   0:0] data$002$clk;
  wire   [   0:0] data$002$en;
  wire   [  15:0] data$002$out;

  RegEn_0x68db79c4ec1d6e5b data$002
  (
    .reset ( data$002$reset ),
    .in_   ( data$002$in_ ),
    .clk   ( data$002$clk ),
    .en    ( data$002$en ),
    .out   ( data$002$out )
  );

  // data$003 temporaries
  wire   [   0:0] data$003$reset;
  wire   [  15:0] data$003$in_;
  wire   [   0:0] data$003$clk;
  wire   [   0:0] data$003$en;
  wire   [  15:0] data$003$out;

  RegEn_0x68db79c4ec1d6e5b data$003
  (
    .reset ( data$003$reset ),
    .in_   ( data$003$in_ ),
    .clk   ( data$003$clk ),
    .en    ( data$003$en ),
    .out   ( data$003$out )
  );

  // signal connections
  assign data$000$clk   = clk;
  assign data$000$reset = reset;
  assign data$001$clk   = clk;
  assign data$001$reset = reset;
  assign data$002$clk   = clk;
  assign data$002$reset = reset;
  assign data$003$clk   = clk;
  assign data$003$reset = reset;
  assign head$clk       = clk;
  assign head$reset     = reset;
  assign num$clk        = clk;
  assign num$reset      = reset;

  // array declarations
  reg    [   0:0] data$en[0:3];
  assign data$000$en = data$en[  0];
  assign data$001$en = data$en[  1];
  assign data$002$en = data$en[  2];
  assign data$003$en = data$en[  3];
  reg    [  15:0] data$in_[0:3];
  assign data$000$in_ = data$in_[  0];
  assign data$001$in_ = data$in_[  1];
  assign data$002$in_ = data$in_[  2];
  assign data$003$in_ = data$in_[  3];
  wire   [  15:0] data$out[0:3];
  assign data$out[  0] = data$000$out;
  assign data$out[  1] = data$001$out;
  assign data$out[  2] = data$002$out;
  assign data$out[  3] = data$003$out;

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update():
  //       s.empty.v = s.num.out == 0
  //
  //       # Ready signals:
  //       s.alloc_port.rdy.v = s.num.out < NUM_ENTRIES  # Alloc rdy
  //       s.update_port.rdy.v = not s.empty
  //       s.remove_port.rdy.v = not s.empty
  //       s.peek_port.rdy.v = not s.empty
  //
  //       # Default rets
  //       s.peek_port.value.v = 0
  //       s.alloc_port.index.v = 0
  //
  //       # Set enables to regs to false
  //       for i in range( NUM_ENTRIES ):
  //         s.data[ i ].en.v = 0
  //
  //       # Mod arithmetic will handle overflow
  //       s.next_slot.v = s.head.out + s.num.out[ 0:IDX_NBITS ]
  //       s.num_next.v = s.num.out
  //       s.head.in_.v = s.head.out
  //
  //       if s.alloc_port.call:  # Alloc an entry
  //         s.num_next.v += 1  # Incr count
  //         s.data[ s.next_slot ].en.v = 1
  //         s.data[ s.next_slot ].in_.v = s.alloc_port.value.v
  //         s.alloc_port.index.v = s.next_slot
  //       if s.update_port.call:  # Update an entry
  //         s.data[ s.update_port.index ].en.v = 1
  //         s.data[ s.update_port.index ].in_.v = s.update_port.value.v
  //       if s.remove_port.call:  # Remove head
  //         s.num_next.v -= 1
  //         s.head.in_.v = s.head.out + 1
  //       if s.peek_port.call:  # Peek at entry
  //         s.peek_port.value.v = s.data[ s.head.out ].out
  //
  //       s.num.in_.v = s.num_next

  // logic for update()
  always @ (*) begin
    empty = (num$out == 0);
    alloc_port_rdy = (num$out < NUM_ENTRIES);
    update_port_rdy = !empty;
    remove_port_rdy = !empty;
    peek_port_rdy = !empty;
    peek_port_value = 0;
    alloc_port_index = 0;
    for (i=0; i < NUM_ENTRIES; i=i+1)
    begin
      data$en[i] = 0;
    end
    next_slot = (head$out+num$out[(IDX_NBITS)-1:0]);
    num_next = num$out;
    head$in_ = head$out;
    if (alloc_port_call) begin
      num_next = num_next + 1;
      data$en[next_slot] = 1;
      data$in_[next_slot] = alloc_port_value;
      alloc_port_index = next_slot;
    end
    else begin
    end
    if (update_port_call) begin
      data$en[update_port_index] = 1;
      data$in_[update_port_index] = update_port_value;
    end
    else begin
    end
    if (remove_port_call) begin
      num_next = num_next - 1;
      head$in_ = (head$out+1);
    end
    else begin
    end
    if (peek_port_call) begin
      peek_port_value = data$out[head$out];
    end
    else begin
    end
    num$in_ = num_next;
  end


endmodule // RingBuffer_0x64da68b78203a525
`default_nettype wire

//-----------------------------------------------------------------------------
// RegRst_0x1099485158c4776f
//-----------------------------------------------------------------------------
// dtype: 3
// reset_value: 0
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegRst_0x1099485158c4776f
(
  input  wire [   0:0] clk,
  input  wire [   2:0] in_,
  output reg  [   2:0] out,
  input  wire [   0:0] reset
);

  // localparam declarations
  localparam reset_value = 0;



  // PYMTL SOURCE:
  //
  // @s.posedge_clk
  // def seq_logic():
  //       if s.reset:
  //         s.out.next = reset_value
  //       else:
  //         s.out.next = s.in_

  // logic for seq_logic()
  always @ (posedge clk) begin
    if (reset) begin
      out <= reset_value;
    end
    else begin
      out <= in_;
    end
  end


endmodule // RegRst_0x1099485158c4776f
`default_nettype wire

//-----------------------------------------------------------------------------
// RegRst_0x9f365fdf6c8998a
//-----------------------------------------------------------------------------
// dtype: 2
// reset_value: 0
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegRst_0x9f365fdf6c8998a
(
  input  wire [   0:0] clk,
  input  wire [   1:0] in_,
  output reg  [   1:0] out,
  input  wire [   0:0] reset
);

  // localparam declarations
  localparam reset_value = 0;



  // PYMTL SOURCE:
  //
  // @s.posedge_clk
  // def seq_logic():
  //       if s.reset:
  //         s.out.next = reset_value
  //       else:
  //         s.out.next = s.in_

  // logic for seq_logic()
  always @ (posedge clk) begin
    if (reset) begin
      out <= reset_value;
    end
    else begin
      out <= in_;
    end
  end


endmodule // RegRst_0x9f365fdf6c8998a
`default_nettype wire

//-----------------------------------------------------------------------------
// RegEn_0x68db79c4ec1d6e5b
//-----------------------------------------------------------------------------
// dtype: 16
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegEn_0x68db79c4ec1d6e5b
(
  input  wire [   0:0] clk,
  input  wire [   0:0] en,
  input  wire [  15:0] in_,
  output reg  [  15:0] out,
  input  wire [   0:0] reset
);



  // PYMTL SOURCE:
  //
  // @s.posedge_clk
  // def seq_logic():
  //       if s.en:
  //         s.out.next = s.in_

  // logic for seq_logic()
  always @ (posedge clk) begin
    if (en) begin
      out <= in_;
    end
    else begin
    end
  end


endmodule // RegEn_0x68db79c4ec1d6e5b
`default_nettype wire

