//-----------------------------------------------------------------------------
// FreeList_0x38e2301998fffd72
//-----------------------------------------------------------------------------
// nslots: 4
// num_alloc_ports: 1
// num_free_ports: 1
// combinational_bypass: False
// used_slots_initial: 0
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module FreeList_0x38e2301998fffd72
(
  input  wire [   0:0] alloc_ports$000_call,
  output wire [   1:0] alloc_ports$000_index,
  output wire [   0:0] alloc_ports$000_rdy,
  input  wire [   0:0] clk,
  input  wire [   0:0] free_ports$000_call,
  input  wire [   1:0] free_ports$000_index,
  input  wire [   0:0] reset
);

  // wire declarations
  wire   [   2:0] free_size_next$000;
  wire   [   1:0] tail_next$000;
  wire   [   1:0] head_next$000;
  wire   [   2:0] alloc_size_next$000;
  wire   [   1:0] workaround_head_incs_inc_out$000;
  wire   [   1:0] workaround_tail_incs_inc_out$000;


  // register declarations
  reg    [   2:0] base__1;
  reg    [   2:0] base__3;
  reg    [   2:0] bypassed_size;
  reg    [   1:0] chead__3;
  reg    [   1:0] ctail__1;
  reg    [   1:0] head;
  reg    [   2:0] size;
  reg    [   1:0] tail;

  // localparam declarations
  localparam nslots = 4;
  localparam num_alloc_ports = 1;
  localparam num_free_ports = 1;
  localparam used_slots_initial = 0;

  // tail_incs$000 temporaries
  wire   [   0:0] tail_incs$000$reset;
  wire   [   0:0] tail_incs$000$clk;
  wire   [   1:0] tail_incs$000$inc_in_;
  wire   [   1:0] tail_incs$000$inc_out;

  WrapInc_0x1e78bd01b0125419 tail_incs$000
  (
    .reset   ( tail_incs$000$reset ),
    .clk     ( tail_incs$000$clk ),
    .inc_in_ ( tail_incs$000$inc_in_ ),
    .inc_out ( tail_incs$000$inc_out )
  );

  // head_incs$000 temporaries
  wire   [   0:0] head_incs$000$reset;
  wire   [   0:0] head_incs$000$clk;
  wire   [   1:0] head_incs$000$inc_in_;
  wire   [   1:0] head_incs$000$inc_out;

  WrapInc_0x1e78bd01b0125419 head_incs$000
  (
    .reset   ( head_incs$000$reset ),
    .clk     ( head_incs$000$clk ),
    .inc_in_ ( head_incs$000$inc_in_ ),
    .inc_out ( head_incs$000$inc_out )
  );

  // free temporaries
  wire   [   0:0] free$clk;
  wire   [   1:0] free$wr_ports$000_addr;
  wire   [   0:0] free$wr_ports$000_call;
  wire   [   1:0] free$wr_ports$000_data;
  wire   [   0:0] free$reset;
  wire   [   1:0] free$rd_ports$000_addr;
  wire   [   1:0] free$rd_ports$000_data;

  RegisterFile_0x6c660f6a4a4515bc free
  (
    .clk               ( free$clk ),
    .wr_ports$000_addr ( free$wr_ports$000_addr ),
    .wr_ports$000_call ( free$wr_ports$000_call ),
    .wr_ports$000_data ( free$wr_ports$000_data ),
    .reset             ( free$reset ),
    .rd_ports$000_addr ( free$rd_ports$000_addr ),
    .rd_ports$000_data ( free$rd_ports$000_data )
  );

  // signal connections
  assign alloc_ports$000_index            = free$rd_ports$000_data;
  assign free$clk                         = clk;
  assign free$reset                       = reset;
  assign head_incs$000$clk                = clk;
  assign head_incs$000$inc_in_            = head;
  assign head_incs$000$reset              = reset;
  assign tail_incs$000$clk                = clk;
  assign tail_incs$000$inc_in_            = tail;
  assign tail_incs$000$reset              = reset;
  assign workaround_head_incs_inc_out$000 = head_incs$000$inc_out;
  assign workaround_tail_incs_inc_out$000 = tail_incs$000$inc_out;

  // array declarations
  wire   [   0:0] alloc_ports_call[0:0];
  assign alloc_ports_call[  0] = alloc_ports$000_call;
  reg    [   0:0] alloc_ports_rdy[0:0];
  assign alloc_ports$000_rdy = alloc_ports_rdy[  0];
  reg    [   2:0] alloc_size_next[0:0];
  assign alloc_size_next$000 = alloc_size_next[  0];
  reg    [   1:0] free$rd_ports_addr[0:0];
  assign free$rd_ports$000_addr = free$rd_ports_addr[  0];
  reg    [   1:0] free$wr_ports_addr[0:0];
  assign free$wr_ports$000_addr = free$wr_ports_addr[  0];
  reg    [   0:0] free$wr_ports_call[0:0];
  assign free$wr_ports$000_call = free$wr_ports_call[  0];
  reg    [   1:0] free$wr_ports_data[0:0];
  assign free$wr_ports$000_data = free$wr_ports_data[  0];
  wire   [   0:0] free_ports_call[0:0];
  assign free_ports_call[  0] = free_ports$000_call;
  wire   [   1:0] free_ports_index[0:0];
  assign free_ports_index[  0] = free_ports$000_index;
  reg    [   2:0] free_size_next[0:0];
  assign free_size_next$000 = free_size_next[  0];
  reg    [   1:0] head_next[0:0];
  assign head_next$000 = head_next[  0];
  reg    [   1:0] tail_next[0:0];
  assign tail_next$000 = tail_next[  0];
  wire   [   1:0] workaround_head_incs_inc_out[0:0];
  assign workaround_head_incs_inc_out[  0] = workaround_head_incs_inc_out$000;
  wire   [   1:0] workaround_tail_incs_inc_out[0:0];
  assign workaround_tail_incs_inc_out[  0] = workaround_tail_incs_inc_out$000;

  // PYMTL SOURCE:
  //
  // @s.tick_rtl
  // def update():
  //       if s.reset:
  //         s.head.n = used_slots_initial
  //         s.tail.n = 0
  //         s.size.n = used_slots_initial
  //       else:
  //         s.head.n = s.head_next[ num_alloc_ports - 1 ]
  //         s.tail.n = s.tail_next[ num_free_ports - 1 ]
  //         s.size.n = s.alloc_size_next[ num_alloc_ports - 1 ]

  // logic for update()
  always @ (posedge clk) begin
    if (reset) begin
      head <= used_slots_initial;
      tail <= 0;
      size <= used_slots_initial;
    end
    else begin
      head <= head_next[(num_alloc_ports-1)];
      tail <= tail_next[(num_free_ports-1)];
      size <= alloc_size_next[(num_alloc_ports-1)];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_free( port=port ):
  //         if port == 0:
  //           base = s.size
  //           ctail = s.tail
  //         else:
  //           base = s.free_size_next[ port - 1 ]
  //           ctail = s.tail_next[ port - 1 ]
  //
  //         if s.free_ports[ port ].call:
  //           s.free.wr_ports[ port ].call.v = 1
  //           s.free.wr_ports[ port ].addr.v = ctail
  //           s.free.wr_ports[ port ].data.v = s.free_ports[ port ].index
  //
  //           s.tail_next[ port ].v = s.workaround_tail_incs_inc_out[ port ]
  //           s.free_size_next[ port ].v = base - 1
  //         else:
  //           s.free.wr_ports[ port ].call.v = 0
  //           s.tail_next[ port ].v = ctail
  //           s.free_size_next[ port ].v = base

  // logic for handle_free()
  always @ (*) begin
    if ((port == 0)) begin
      base__1 = size;
      ctail__1 = tail;
    end
    else begin
      base__1 = free_size_next[(port-1)];
      ctail__1 = tail_next[(port-1)];
    end
    if (free_ports_call[port]) begin
      free$wr_ports_call[port] = 1;
      free$wr_ports_addr[port] = ctail__1;
      free$wr_ports_data[port] = free_ports_index[port];
      tail_next[port] = workaround_tail_incs_inc_out[port];
      free_size_next[port] = (base__1-1);
    end
    else begin
      free$wr_ports_call[port] = 0;
      tail_next[port] = ctail__1;
      free_size_next[port] = base__1;
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_bypass():
  //         s.bypassed_size.v = s.size

  // logic for handle_bypass()
  always @ (*) begin
    bypassed_size = size;
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_alloc( port=port ):
  //         if port == 0:
  //           base = s.free_size_next[ num_free_ports - 1 ]
  //           chead = s.head
  //         else:
  //           base = s.alloc_size_next[ port - 1 ]
  //           chead = s.head_next[ port - 1 ]
  //         s.free.rd_ports[ port ].addr.v = chead
  //         s.alloc_ports[ port ].rdy.v = ( s.bypassed_size != nslots )
  //         if s.alloc_ports[ port ].call:
  //           s.head_next[ port ].v = s.workaround_head_incs_inc_out[ port ]
  //           s.alloc_size_next[ port ].v = base + 1
  //         else:
  //           s.head_next[ port ].v = chead
  //           s.alloc_size_next[ port ].v = base

  // logic for handle_alloc()
  always @ (*) begin
    if ((port == 0)) begin
      base__3 = free_size_next[(num_free_ports-1)];
      chead__3 = head;
    end
    else begin
      base__3 = alloc_size_next[(port-1)];
      chead__3 = head_next[(port-1)];
    end
    free$rd_ports_addr[port] = chead__3;
    alloc_ports_rdy[port] = (bypassed_size != nslots);
    if (alloc_ports_call[port]) begin
      head_next[port] = workaround_head_incs_inc_out[port];
      alloc_size_next[port] = (base__3+1);
    end
    else begin
      head_next[port] = chead__3;
      alloc_size_next[port] = base__3;
    end
  end


endmodule // FreeList_0x38e2301998fffd72
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

//-----------------------------------------------------------------------------
// RegisterFile_0x6c660f6a4a4515bc
//-----------------------------------------------------------------------------
// dtype: 2
// nregs: 4
// num_rd_ports: 1
// num_wr_ports: 1
// combinational_read_bypass: False
// dump_port: False
// reset_values: [<pymtl.model.signals.Wire object at 0x7fd692315a90>, <pymtl.model.signals.Wire object at 0x7fd692315c90>, <pymtl.model.signals.Wire object at 0x7fd692315790>, <pymtl.model.signals.Wire object at 0x7fd692315690>]
// combinational_dump_read_bypass: False
// combinational_dump_bypass: False
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegisterFile_0x6c660f6a4a4515bc
(
  input  wire [   0:0] clk,
  input  wire [   1:0] rd_ports$000_addr,
  output wire [   1:0] rd_ports$000_data,
  input  wire [   0:0] reset,
  input  wire [   1:0] wr_ports$000_addr,
  input  wire [   0:0] wr_ports$000_call,
  input  wire [   1:0] wr_ports$000_data
);

  // wire declarations
  wire   [   1:0] reset_values$000;
  wire   [   1:0] reset_values$001;
  wire   [   1:0] reset_values$002;
  wire   [   1:0] reset_values$003;
  wire   [   1:0] regs_next_last$000;
  wire   [   1:0] regs_next_last$001;
  wire   [   1:0] regs_next_last$002;
  wire   [   1:0] regs_next_last$003;
  wire   [   1:0] regs_next$000;
  wire   [   1:0] regs_next$001;
  wire   [   1:0] regs_next$002;
  wire   [   1:0] regs_next$003;
  wire   [   1:0] regs$000;
  wire   [   1:0] regs$001;
  wire   [   1:0] regs$002;
  wire   [   1:0] regs$003;
  wire   [   1:0] regs_next_dump$000;
  wire   [   1:0] regs_next_dump$001;
  wire   [   1:0] regs_next_dump$002;
  wire   [   1:0] regs_next_dump$003;


  // signal connections
  assign reset_values$000 = 2'd0;
  assign reset_values$001 = 2'd1;
  assign reset_values$002 = 2'd2;
  assign reset_values$003 = 2'd3;

  // array declarations
  wire   [   1:0] rd_ports_addr[0:0];
  assign rd_ports_addr[  0] = rd_ports$000_addr;
  reg    [   1:0] rd_ports_data[0:0];
  assign rd_ports$000_data = rd_ports_data[  0];
  reg    [   1:0] regs[0:3];
  assign regs$000 = regs[  0];
  assign regs$001 = regs[  1];
  assign regs$002 = regs[  2];
  assign regs$003 = regs[  3];
  reg    [   1:0] regs_next[0:3];
  assign regs_next$000 = regs_next[  0];
  assign regs_next$001 = regs_next[  1];
  assign regs_next$002 = regs_next[  2];
  assign regs_next$003 = regs_next[  3];
  reg    [   1:0] regs_next_dump[0:3];
  assign regs_next_dump$000 = regs_next_dump[  0];
  assign regs_next_dump$001 = regs_next_dump[  1];
  assign regs_next_dump$002 = regs_next_dump[  2];
  assign regs_next_dump$003 = regs_next_dump[  3];
  reg    [   1:0] regs_next_last[0:3];
  assign regs_next_last$000 = regs_next_last[  0];
  assign regs_next_last$001 = regs_next_last[  1];
  assign regs_next_last$002 = regs_next_last[  2];
  assign regs_next_last$003 = regs_next_last[  3];
  wire   [   1:0] reset_values[0:3];
  assign reset_values[  0] = reset_values$000;
  assign reset_values[  1] = reset_values$001;
  assign reset_values[  2] = reset_values$002;
  assign reset_values[  3] = reset_values$003;
  wire   [   1:0] wr_ports_addr[0:0];
  assign wr_ports_addr[  0] = wr_ports$000_addr;
  wire   [   0:0] wr_ports_call[0:0];
  assign wr_ports_call[  0] = wr_ports$000_call;
  wire   [   1:0] wr_ports_data[0:0];
  assign wr_ports_data[  0] = wr_ports$000_data;

  // PYMTL SOURCE:
  //
  // @s.tick_rtl
  // def update( reg_i=reg_i ):
  //         if s.reset:
  //           s.regs[ reg_i ].n = s.reset_values[ reg_i ]
  //         else:
  //           s.regs[ reg_i ].n = s.regs_next_dump[ reg_i ]

  // logic for update()
  always @ (posedge clk) begin
    if (reset) begin
      regs[reg_i] <= reset_values[reg_i];
    end
    else begin
      regs[reg_i] <= regs_next_dump[reg_i];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.tick_rtl
  // def update( reg_i=reg_i ):
  //         if s.reset:
  //           s.regs[ reg_i ].n = s.reset_values[ reg_i ]
  //         else:
  //           s.regs[ reg_i ].n = s.regs_next_dump[ reg_i ]

  // logic for update()
  always @ (posedge clk) begin
    if (reset) begin
      regs[reg_i] <= reset_values[reg_i];
    end
    else begin
      regs[reg_i] <= regs_next_dump[reg_i];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.tick_rtl
  // def update( reg_i=reg_i ):
  //         if s.reset:
  //           s.regs[ reg_i ].n = s.reset_values[ reg_i ]
  //         else:
  //           s.regs[ reg_i ].n = s.regs_next_dump[ reg_i ]

  // logic for update()
  always @ (posedge clk) begin
    if (reset) begin
      regs[reg_i] <= reset_values[reg_i];
    end
    else begin
      regs[reg_i] <= regs_next_dump[reg_i];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.tick_rtl
  // def update( reg_i=reg_i ):
  //         if s.reset:
  //           s.regs[ reg_i ].n = s.reset_values[ reg_i ]
  //         else:
  //           s.regs[ reg_i ].n = s.regs_next_dump[ reg_i ]

  // logic for update()
  always @ (posedge clk) begin
    if (reset) begin
      regs[reg_i] <= reset_values[reg_i];
    end
    else begin
      regs[reg_i] <= regs_next_dump[reg_i];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_last( reg_i=reg_i, i=( num_wr_ports - 1 ) * nregs + reg_i ):
  //           s.regs_next_last[ reg_i ].v = s.regs_next[ i ]

  // logic for update_last()
  always @ (*) begin
    regs_next_last[reg_i] = regs_next[i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_next_dump( reg_i=reg_i ):
  //           s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

  // logic for update_next_dump()
  always @ (*) begin
    regs_next_dump[reg_i] = regs_next_last[reg_i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_last( reg_i=reg_i, i=( num_wr_ports - 1 ) * nregs + reg_i ):
  //           s.regs_next_last[ reg_i ].v = s.regs_next[ i ]

  // logic for update_last()
  always @ (*) begin
    regs_next_last[reg_i] = regs_next[i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_next_dump( reg_i=reg_i ):
  //           s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

  // logic for update_next_dump()
  always @ (*) begin
    regs_next_dump[reg_i] = regs_next_last[reg_i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_last( reg_i=reg_i, i=( num_wr_ports - 1 ) * nregs + reg_i ):
  //           s.regs_next_last[ reg_i ].v = s.regs_next[ i ]

  // logic for update_last()
  always @ (*) begin
    regs_next_last[reg_i] = regs_next[i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_next_dump( reg_i=reg_i ):
  //           s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

  // logic for update_next_dump()
  always @ (*) begin
    regs_next_dump[reg_i] = regs_next_last[reg_i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_last( reg_i=reg_i, i=( num_wr_ports - 1 ) * nregs + reg_i ):
  //           s.regs_next_last[ reg_i ].v = s.regs_next[ i ]

  // logic for update_last()
  always @ (*) begin
    regs_next_last[reg_i] = regs_next[i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def update_next_dump( reg_i=reg_i ):
  //           s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

  // logic for update_next_dump()
  always @ (*) begin
    regs_next_dump[reg_i] = regs_next_last[reg_i];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_read( port=port ):
  //           s.rd_ports[ port ].data.v = s.regs[ s.rd_ports[ port ].addr ]

  // logic for handle_read()
  always @ (*) begin
    rd_ports_data[port] = regs[rd_ports_addr[port]];
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_write( reg_i=reg_i,
  //                           port=port,
  //                           i=port * nregs + reg_i,
  //                           j=( port - 1 ) * nregs + reg_i ):
  //           if s.wr_ports[ port ].call and s.wr_ports[ port ].addr == reg_i:
  //             s.regs_next[ i ].v = s.wr_ports[ port ].data
  //           elif port == 0:
  //             s.regs_next[ i ].v = s.regs[ reg_i ]
  //           else:
  //             s.regs_next[ i ].v = s.regs_next[ j ]

  // logic for handle_write()
  always @ (*) begin
    if ((wr_ports_call[port]&&(wr_ports_addr[port] == reg_i))) begin
      regs_next[i] = wr_ports_data[port];
    end
    else begin
      if ((port == 0)) begin
        regs_next[i] = regs[reg_i];
      end
      else begin
        regs_next[i] = regs_next[j];
      end
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_write( reg_i=reg_i,
  //                           port=port,
  //                           i=port * nregs + reg_i,
  //                           j=( port - 1 ) * nregs + reg_i ):
  //           if s.wr_ports[ port ].call and s.wr_ports[ port ].addr == reg_i:
  //             s.regs_next[ i ].v = s.wr_ports[ port ].data
  //           elif port == 0:
  //             s.regs_next[ i ].v = s.regs[ reg_i ]
  //           else:
  //             s.regs_next[ i ].v = s.regs_next[ j ]

  // logic for handle_write()
  always @ (*) begin
    if ((wr_ports_call[port]&&(wr_ports_addr[port] == reg_i))) begin
      regs_next[i] = wr_ports_data[port];
    end
    else begin
      if ((port == 0)) begin
        regs_next[i] = regs[reg_i];
      end
      else begin
        regs_next[i] = regs_next[j];
      end
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_write( reg_i=reg_i,
  //                           port=port,
  //                           i=port * nregs + reg_i,
  //                           j=( port - 1 ) * nregs + reg_i ):
  //           if s.wr_ports[ port ].call and s.wr_ports[ port ].addr == reg_i:
  //             s.regs_next[ i ].v = s.wr_ports[ port ].data
  //           elif port == 0:
  //             s.regs_next[ i ].v = s.regs[ reg_i ]
  //           else:
  //             s.regs_next[ i ].v = s.regs_next[ j ]

  // logic for handle_write()
  always @ (*) begin
    if ((wr_ports_call[port]&&(wr_ports_addr[port] == reg_i))) begin
      regs_next[i] = wr_ports_data[port];
    end
    else begin
      if ((port == 0)) begin
        regs_next[i] = regs[reg_i];
      end
      else begin
        regs_next[i] = regs_next[j];
      end
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_write( reg_i=reg_i,
  //                           port=port,
  //                           i=port * nregs + reg_i,
  //                           j=( port - 1 ) * nregs + reg_i ):
  //           if s.wr_ports[ port ].call and s.wr_ports[ port ].addr == reg_i:
  //             s.regs_next[ i ].v = s.wr_ports[ port ].data
  //           elif port == 0:
  //             s.regs_next[ i ].v = s.regs[ reg_i ]
  //           else:
  //             s.regs_next[ i ].v = s.regs_next[ j ]

  // logic for handle_write()
  always @ (*) begin
    if ((wr_ports_call[port]&&(wr_ports_addr[port] == reg_i))) begin
      regs_next[i] = wr_ports_data[port];
    end
    else begin
      if ((port == 0)) begin
        regs_next[i] = regs[reg_i];
      end
      else begin
        regs_next[i] = regs_next[j];
      end
    end
  end


endmodule // RegisterFile_0x6c660f6a4a4515bc
`default_nettype wire

