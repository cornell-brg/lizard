//-----------------------------------------------------------------------------
// RegisterFile_0x6a232bd299deb57c
//-----------------------------------------------------------------------------
// dtype: 8
// nregs: 2
// num_rd_ports: 1
// num_wr_ports: 1
// combinational_read_bypass: False
// dump_port: True
// reset_values: None
// combinational_dump_read_bypass: False
// combinational_dump_bypass: False
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module RegisterFile_0x6a232bd299deb57c
(
  input  wire [   0:0] clk,
  input  wire [   7:0] dump_in$000,
  input  wire [   7:0] dump_in$001,
  output wire [   7:0] dump_out$000,
  output wire [   7:0] dump_out$001,
  input  wire [   0:0] dump_wr_en,
  input  wire [   0:0] rd_ports$000_addr,
  output wire [   7:0] rd_ports$000_data,
  input  wire [   0:0] reset,
  input  wire [   0:0] wr_ports$000_addr,
  input  wire [   0:0] wr_ports$000_call,
  input  wire [   7:0] wr_ports$000_data
);

  // wire declarations
  wire   [   7:0] reset_values$000;
  wire   [   7:0] reset_values$001;
  wire   [   7:0] regs_next_last$000;
  wire   [   7:0] regs_next_last$001;
  wire   [   7:0] regs_next$000;
  wire   [   7:0] regs_next$001;
  wire   [   7:0] regs$000;
  wire   [   7:0] regs$001;
  wire   [   7:0] regs_next_dump$000;
  wire   [   7:0] regs_next_dump$001;


  // signal connections
  assign dump_out$000     = regs$000;
  assign dump_out$001     = regs$001;
  assign reset_values$000 = 8'd0;
  assign reset_values$001 = 8'd0;

  // array declarations
  wire   [   7:0] dump_in[0:1];
  assign dump_in[  0] = dump_in$000;
  assign dump_in[  1] = dump_in$001;
  wire   [   0:0] rd_ports_addr[0:0];
  assign rd_ports_addr[  0] = rd_ports$000_addr;
  reg    [   7:0] rd_ports_data[0:0];
  assign rd_ports$000_data = rd_ports_data[  0];
  reg    [   7:0] regs[0:1];
  assign regs$000 = regs[  0];
  assign regs$001 = regs[  1];
  reg    [   7:0] regs_next[0:1];
  assign regs_next$000 = regs_next[  0];
  assign regs_next$001 = regs_next[  1];
  reg    [   7:0] regs_next_dump[0:1];
  assign regs_next_dump$000 = regs_next_dump[  0];
  assign regs_next_dump$001 = regs_next_dump[  1];
  reg    [   7:0] regs_next_last[0:1];
  assign regs_next_last$000 = regs_next_last[  0];
  assign regs_next_last$001 = regs_next_last[  1];
  wire   [   7:0] reset_values[0:1];
  assign reset_values[  0] = reset_values$000;
  assign reset_values[  1] = reset_values$001;
  wire   [   0:0] wr_ports_addr[0:0];
  assign wr_ports_addr[  0] = wr_ports$000_addr;
  wire   [   0:0] wr_ports_call[0:0];
  assign wr_ports_call[  0] = wr_ports$000_call;
  wire   [   7:0] wr_ports_data[0:0];
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
  //           if s.dump_wr_en:
  //             s.regs_next_dump[ reg_i ].v = s.dump_in[ reg_i ]
  //           else:
  //             s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

  // logic for update_next_dump()
  always @ (*) begin
    if (dump_wr_en) begin
      regs_next_dump[reg_i] = dump_in[reg_i];
    end
    else begin
      regs_next_dump[reg_i] = regs_next_last[reg_i];
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
  //           if s.dump_wr_en:
  //             s.regs_next_dump[ reg_i ].v = s.dump_in[ reg_i ]
  //           else:
  //             s.regs_next_dump[ reg_i ].v = s.regs_next_last[ reg_i ]

  // logic for update_next_dump()
  always @ (*) begin
    if (dump_wr_en) begin
      regs_next_dump[reg_i] = dump_in[reg_i];
    end
    else begin
      regs_next_dump[reg_i] = regs_next_last[reg_i];
    end
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


endmodule // RegisterFile_0x6a232bd299deb57c
`default_nettype wire

