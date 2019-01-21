//-----------------------------------------------------------------------------
// RenameTable_0x64843d55f426bb52
//-----------------------------------------------------------------------------
// naregs: 2
// npregs: 4
// nread_ports: 2
// nwrite_ports: 1
// nsnapshots: 1
// const_zero: True
// initial_map: [<pymtl.model.signals.Wire object at 0x7fd692c50d50>, <pymtl.model.signals.Wire object at 0x7fd692c50650>]
// dump-vcd: True
// verilator-xinit: zeros
`default_nettype none
module RenameTable_0x64843d55f426bb52
(
  input  wire [   0:0] clk,
  input  wire [   0:0] external_restore_en,
  input  wire [   1:0] external_restore_in$000,
  input  wire [   1:0] external_restore_in$001,
  input  wire [   0:0] free_snapshot_port_call,
  input  wire [   0:0] free_snapshot_port_id,
  input  wire [   0:0] read_ports$000_areg,
  output wire [   1:0] read_ports$000_preg,
  input  wire [   0:0] read_ports$001_areg,
  output wire [   1:0] read_ports$001_preg,
  input  wire [   0:0] reset,
  input  wire [   0:0] restore_port_call,
  input  wire [   0:0] restore_port_id,
  input  wire [   0:0] snapshot_port_call,
  output wire [   0:0] snapshot_port_id,
  output wire [   0:0] snapshot_port_rdy,
  input  wire [   0:0] write_ports$000_areg,
  input  wire [   0:0] write_ports$000_call,
  input  wire [   1:0] write_ports$000_preg
);

  // localparam declarations
  localparam ZERO_TAG = 2'd3;

  // rename_table temporaries
  wire   [   0:0] rename_table$external_restore_en;
  wire   [   0:0] rename_table$free_snapshot_port_call;
  wire   [   0:0] rename_table$free_snapshot_port_id;
  wire   [   1:0] rename_table$external_restore_in$000;
  wire   [   1:0] rename_table$external_restore_in$001;
  wire   [   0:0] rename_table$clk;
  wire   [   0:0] rename_table$snapshot_port_call;
  wire   [   0:0] rename_table$wr_ports$000_addr;
  wire   [   0:0] rename_table$wr_ports$000_call;
  wire   [   1:0] rename_table$wr_ports$000_data;
  wire   [   0:0] rename_table$restore_port_call;
  wire   [   0:0] rename_table$restore_port_id;
  wire   [   0:0] rename_table$reset;
  wire   [   0:0] rename_table$rd_ports$000_addr;
  wire   [   0:0] rename_table$rd_ports$001_addr;
  wire   [   0:0] rename_table$snapshot_port_id;
  wire   [   0:0] rename_table$snapshot_port_rdy;
  wire   [   1:0] rename_table$rd_ports$000_data;
  wire   [   1:0] rename_table$rd_ports$001_data;

  SnapshottingRegisterFile_0x4354a37749e4a113 rename_table
  (
    .external_restore_en     ( rename_table$external_restore_en ),
    .free_snapshot_port_call ( rename_table$free_snapshot_port_call ),
    .free_snapshot_port_id   ( rename_table$free_snapshot_port_id ),
    .external_restore_in$000 ( rename_table$external_restore_in$000 ),
    .external_restore_in$001 ( rename_table$external_restore_in$001 ),
    .clk                     ( rename_table$clk ),
    .snapshot_port_call      ( rename_table$snapshot_port_call ),
    .wr_ports$000_addr       ( rename_table$wr_ports$000_addr ),
    .wr_ports$000_call       ( rename_table$wr_ports$000_call ),
    .wr_ports$000_data       ( rename_table$wr_ports$000_data ),
    .restore_port_call       ( rename_table$restore_port_call ),
    .restore_port_id         ( rename_table$restore_port_id ),
    .reset                   ( rename_table$reset ),
    .rd_ports$000_addr       ( rename_table$rd_ports$000_addr ),
    .rd_ports$001_addr       ( rename_table$rd_ports$001_addr ),
    .snapshot_port_id        ( rename_table$snapshot_port_id ),
    .snapshot_port_rdy       ( rename_table$snapshot_port_rdy ),
    .rd_ports$000_data       ( rename_table$rd_ports$000_data ),
    .rd_ports$001_data       ( rename_table$rd_ports$001_data )
  );

  // signal connections
  assign rename_table$clk                     = clk;
  assign rename_table$external_restore_en     = external_restore_en;
  assign rename_table$external_restore_in$000 = external_restore_in$000;
  assign rename_table$external_restore_in$001 = external_restore_in$001;
  assign rename_table$free_snapshot_port_call = free_snapshot_port_call;
  assign rename_table$free_snapshot_port_id   = free_snapshot_port_id;
  assign rename_table$rd_ports$000_addr       = read_ports$000_areg;
  assign rename_table$rd_ports$001_addr       = read_ports$001_areg;
  assign rename_table$reset                   = reset;
  assign rename_table$restore_port_call       = restore_port_call;
  assign rename_table$restore_port_id         = restore_port_id;
  assign rename_table$snapshot_port_call      = snapshot_port_call;
  assign rename_table$wr_ports$000_addr       = write_ports$000_areg;
  assign rename_table$wr_ports$000_data       = write_ports$000_preg;
  assign snapshot_port_id                     = rename_table$snapshot_port_id;
  assign snapshot_port_rdy                    = rename_table$snapshot_port_rdy;

  // array declarations
  wire   [   0:0] read_ports_areg[0:1];
  assign read_ports_areg[  0] = read_ports$000_areg;
  assign read_ports_areg[  1] = read_ports$001_areg;
  reg    [   1:0] read_ports_preg[0:1];
  assign read_ports$000_preg = read_ports_preg[  0];
  assign read_ports$001_preg = read_ports_preg[  1];
  wire   [   1:0] rename_table$rd_ports_data[0:1];
  assign rename_table$rd_ports_data[  0] = rename_table$rd_ports$000_data;
  assign rename_table$rd_ports_data[  1] = rename_table$rd_ports$001_data;
  reg    [   0:0] rename_table$wr_ports_call[0:0];
  assign rename_table$wr_ports$000_call = rename_table$wr_ports_call[  0];
  wire   [   0:0] write_ports_areg[0:0];
  assign write_ports_areg[  0] = write_ports$000_areg;
  wire   [   0:0] write_ports_call[0:0];
  assign write_ports_call[  0] = write_ports$000_call;

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_zero_read( i=i ):
  //           if s.read_ports[ i ].areg == 0:
  //             s.read_ports[ i ].preg.v = s.ZERO_TAG
  //           else:
  //             s.read_ports[ i ].preg.v = s.rename_table.rd_ports[ i ].data

  // logic for handle_zero_read()
  always @ (*) begin
    if ((read_ports_areg[i] == 0)) begin
      read_ports_preg[i] = ZERO_TAG;
    end
    else begin
      read_ports_preg[i] = rename_table$rd_ports_data[i];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_zero_read( i=i ):
  //           if s.read_ports[ i ].areg == 0:
  //             s.read_ports[ i ].preg.v = s.ZERO_TAG
  //           else:
  //             s.read_ports[ i ].preg.v = s.rename_table.rd_ports[ i ].data

  // logic for handle_zero_read()
  always @ (*) begin
    if ((read_ports_areg[i] == 0)) begin
      read_ports_preg[i] = ZERO_TAG;
    end
    else begin
      read_ports_preg[i] = rename_table$rd_ports_data[i];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_zero_write( i=i ):
  //           if s.write_ports[ i ].areg == 0:
  //             s.rename_table.wr_ports[ i ].call.v = 0
  //           else:
  //             s.rename_table.wr_ports[ i ].call.v = s.write_ports[ i ].call

  // logic for handle_zero_write()
  always @ (*) begin
    if ((write_ports_areg[i] == 0)) begin
      rename_table$wr_ports_call[i] = 0;
    end
    else begin
      rename_table$wr_ports_call[i] = write_ports_call[i];
    end
  end


endmodule // RenameTable_0x64843d55f426bb52
`default_nettype wire

//-----------------------------------------------------------------------------
// SnapshottingRegisterFile_0x4354a37749e4a113
//-----------------------------------------------------------------------------
// dtype: 2
// nregs: 2
// num_rd_ports: 2
// num_wr_ports: 1
// combinational_read_bypass: False
// nsnapshots: 1
// external_restore: True
// reset_values: [<pymtl.model.signals.Wire object at 0x7fd692c50d50>, <pymtl.model.signals.Wire object at 0x7fd692c50650>]
// combinational_snapshot_bypass: True
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module SnapshottingRegisterFile_0x4354a37749e4a113
(
  input  wire [   0:0] clk,
  input  wire [   0:0] external_restore_en,
  input  wire [   1:0] external_restore_in$000,
  input  wire [   1:0] external_restore_in$001,
  input  wire [   0:0] free_snapshot_port_call,
  input  wire [   0:0] free_snapshot_port_id,
  input  wire [   0:0] rd_ports$000_addr,
  output wire [   1:0] rd_ports$000_data,
  input  wire [   0:0] rd_ports$001_addr,
  output wire [   1:0] rd_ports$001_data,
  input  wire [   0:0] reset,
  input  wire [   0:0] restore_port_call,
  input  wire [   0:0] restore_port_id,
  input  wire [   0:0] snapshot_port_call,
  output wire [   0:0] snapshot_port_id,
  output wire [   0:0] snapshot_port_rdy,
  input  wire [   0:0] wr_ports$000_addr,
  input  wire [   0:0] wr_ports$000_call,
  input  wire [   1:0] wr_ports$000_data
);

  // wire declarations
  wire   [   0:0] snapshot_target;
  wire   [   0:0] taking_snapshot;


  // snapshots$000 temporaries
  wire   [   1:0] snapshots$000$dump_in$000;
  wire   [   1:0] snapshots$000$dump_in$001;
  wire   [   0:0] snapshots$000$clk;
  wire   [   0:0] snapshots$000$reset;
  wire   [   0:0] snapshots$000$dump_wr_en;
  wire   [   1:0] snapshots$000$dump_out$000;
  wire   [   1:0] snapshots$000$dump_out$001;

  RegisterFile_0x32d8e0d9c3795e02 snapshots$000
  (
    .dump_in$000  ( snapshots$000$dump_in$000 ),
    .dump_in$001  ( snapshots$000$dump_in$001 ),
    .clk          ( snapshots$000$clk ),
    .reset        ( snapshots$000$reset ),
    .dump_wr_en   ( snapshots$000$dump_wr_en ),
    .dump_out$000 ( snapshots$000$dump_out$000 ),
    .dump_out$001 ( snapshots$000$dump_out$001 )
  );

  // regs temporaries
  wire   [   1:0] regs$dump_in$000;
  wire   [   1:0] regs$dump_in$001;
  wire   [   0:0] regs$clk;
  wire   [   0:0] regs$wr_ports$000_addr;
  wire   [   0:0] regs$wr_ports$000_call;
  wire   [   1:0] regs$wr_ports$000_data;
  wire   [   0:0] regs$reset;
  wire   [   0:0] regs$dump_wr_en;
  wire   [   0:0] regs$rd_ports$000_addr;
  wire   [   0:0] regs$rd_ports$001_addr;
  wire   [   1:0] regs$rd_ports$000_data;
  wire   [   1:0] regs$rd_ports$001_data;
  wire   [   1:0] regs$dump_out$000;
  wire   [   1:0] regs$dump_out$001;

  RegisterFile_0x410c6f4c3e230ab0 regs
  (
    .dump_in$000       ( regs$dump_in$000 ),
    .dump_in$001       ( regs$dump_in$001 ),
    .clk               ( regs$clk ),
    .wr_ports$000_addr ( regs$wr_ports$000_addr ),
    .wr_ports$000_call ( regs$wr_ports$000_call ),
    .wr_ports$000_data ( regs$wr_ports$000_data ),
    .reset             ( regs$reset ),
    .dump_wr_en        ( regs$dump_wr_en ),
    .rd_ports$000_addr ( regs$rd_ports$000_addr ),
    .rd_ports$001_addr ( regs$rd_ports$001_addr ),
    .rd_ports$000_data ( regs$rd_ports$000_data ),
    .rd_ports$001_data ( regs$rd_ports$001_data ),
    .dump_out$000      ( regs$dump_out$000 ),
    .dump_out$001      ( regs$dump_out$001 )
  );

  // snapshot_allocator temporaries
  wire   [   0:0] snapshot_allocator$clk;
  wire   [   0:0] snapshot_allocator$reset;
  wire   [   0:0] snapshot_allocator$free_ports$000_call;
  wire   [   0:0] snapshot_allocator$free_ports$000_index;
  wire   [   0:0] snapshot_allocator$alloc_ports$000_call;
  wire   [   0:0] snapshot_allocator$alloc_ports$000_index;
  wire   [   0:0] snapshot_allocator$alloc_ports$000_rdy;

  FreeList_0x35f64f2902ec6b0b snapshot_allocator
  (
    .clk                   ( snapshot_allocator$clk ),
    .reset                 ( snapshot_allocator$reset ),
    .free_ports$000_call   ( snapshot_allocator$free_ports$000_call ),
    .free_ports$000_index  ( snapshot_allocator$free_ports$000_index ),
    .alloc_ports$000_call  ( snapshot_allocator$alloc_ports$000_call ),
    .alloc_ports$000_index ( snapshot_allocator$alloc_ports$000_index ),
    .alloc_ports$000_rdy   ( snapshot_allocator$alloc_ports$000_rdy )
  );

  // signal connections
  assign rd_ports$000_data                       = regs$rd_ports$000_data;
  assign rd_ports$001_data                       = regs$rd_ports$001_data;
  assign regs$clk                                = clk;
  assign regs$dump_wr_en                         = restore_port_call;
  assign regs$rd_ports$000_addr                  = rd_ports$000_addr;
  assign regs$rd_ports$001_addr                  = rd_ports$001_addr;
  assign regs$reset                              = reset;
  assign regs$wr_ports$000_addr                  = wr_ports$000_addr;
  assign regs$wr_ports$000_call                  = wr_ports$000_call;
  assign regs$wr_ports$000_data                  = wr_ports$000_data;
  assign snapshot_allocator$alloc_ports$000_call = snapshot_port_call;
  assign snapshot_allocator$clk                  = clk;
  assign snapshot_allocator$free_ports$000_call  = free_snapshot_port_call;
  assign snapshot_allocator$free_ports$000_index = free_snapshot_port_id;
  assign snapshot_allocator$reset                = reset;
  assign snapshot_port_id                        = snapshot_allocator$alloc_ports$000_index;
  assign snapshot_port_rdy                       = snapshot_allocator$alloc_ports$000_rdy;
  assign snapshots$000$clk                       = clk;
  assign snapshots$000$dump_in$000               = regs$dump_out$000;
  assign snapshots$000$dump_in$001               = regs$dump_out$001;
  assign snapshots$000$reset                     = reset;
  assign taking_snapshot                         = snapshot_port_call;

  // array declarations
  wire   [   1:0] external_restore_in[0:1];
  assign external_restore_in[  0] = external_restore_in$000;
  assign external_restore_in[  1] = external_restore_in$001;
  reg    [   1:0] regs$dump_in[0:1];
  assign regs$dump_in$000 = regs$dump_in[  0];
  assign regs$dump_in$001 = regs$dump_in[  1];
  wire   [   0:0] snapshot_allocator$alloc_ports_index[0:0];
  assign snapshot_allocator$alloc_ports_index[  0] = snapshot_allocator$alloc_ports$000_index;
  wire   [   1:0] snapshots$dump_out[0:0][0:1];
  assign snapshots$dump_out[  0][  0] = snapshots$000$dump_out$000;
  assign snapshots$dump_out[  0][  1] = snapshots$000$dump_out$001;
  reg    [   0:0] snapshots$dump_wr_en[0:0];
  assign snapshots$000$dump_wr_en = snapshots$dump_wr_en[  0];

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_snapshot_save( i=i ):
  //         s.snapshots[
  //             i ].dump_wr_en.v = s.taking_snapshot and s.snapshot_allocator.alloc_ports[
  //                 0 ].index == i

  // logic for handle_snapshot_save()
  always @ (*) begin
    snapshots$dump_wr_en[i] = (taking_snapshot&&(snapshot_allocator$alloc_ports_index[0] == i));
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_restore( j=j ):
  //           if s.external_restore_en:
  //             s.regs.dump_in[ j ].v = s.external_restore_in[ j ]
  //           else:
  //             s.regs.dump_in[ j ].v = s.snapshots[ s.restore_port
  //                                                  .id ].dump_out[ j ]

  // logic for handle_restore()
  always @ (*) begin
    if (external_restore_en) begin
      regs$dump_in[j] = external_restore_in[j];
    end
    else begin
      regs$dump_in[j] = snapshots$dump_out[restore_port_id][j];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_restore( j=j ):
  //           if s.external_restore_en:
  //             s.regs.dump_in[ j ].v = s.external_restore_in[ j ]
  //           else:
  //             s.regs.dump_in[ j ].v = s.snapshots[ s.restore_port
  //                                                  .id ].dump_out[ j ]

  // logic for handle_restore()
  always @ (*) begin
    if (external_restore_en) begin
      regs$dump_in[j] = external_restore_in[j];
    end
    else begin
      regs$dump_in[j] = snapshots$dump_out[restore_port_id][j];
    end
  end


endmodule // SnapshottingRegisterFile_0x4354a37749e4a113
`default_nettype wire

//-----------------------------------------------------------------------------
// RegisterFile_0x32d8e0d9c3795e02
//-----------------------------------------------------------------------------
// dtype: 2
// nregs: 2
// num_rd_ports: 0
// num_wr_ports: 0
// combinational_read_bypass: False
// dump_port: True
// reset_values: None
// combinational_dump_read_bypass: False
// combinational_dump_bypass: False
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegisterFile_0x32d8e0d9c3795e02
(
  input  wire [   0:0] clk,
  input  wire [   1:0] dump_in$000,
  input  wire [   1:0] dump_in$001,
  output wire [   1:0] dump_out$000,
  output wire [   1:0] dump_out$001,
  input  wire [   0:0] dump_wr_en,
  input  wire [   0:0] reset
);

  // wire declarations
  wire   [   1:0] reset_values$000;
  wire   [   1:0] reset_values$001;
  wire   [   1:0] regs_next_last$000;
  wire   [   1:0] regs_next_last$001;
  wire   [   1:0] regs$000;
  wire   [   1:0] regs$001;
  wire   [   1:0] regs_next_dump$000;
  wire   [   1:0] regs_next_dump$001;


  // signal connections
  assign dump_out$000     = regs$000;
  assign dump_out$001     = regs$001;
  assign reset_values$000 = 2'd0;
  assign reset_values$001 = 2'd0;

  // array declarations
  wire   [   1:0] dump_in[0:1];
  assign dump_in[  0] = dump_in$000;
  assign dump_in[  1] = dump_in$001;
  reg    [   1:0] regs[0:1];
  assign regs$000 = regs[  0];
  assign regs$001 = regs[  1];
  reg    [   1:0] regs_next_dump[0:1];
  assign regs_next_dump$000 = regs_next_dump[  0];
  assign regs_next_dump$001 = regs_next_dump[  1];
  reg    [   1:0] regs_next_last[0:1];
  assign regs_next_last$000 = regs_next_last[  0];
  assign regs_next_last$001 = regs_next_last[  1];
  wire   [   1:0] reset_values[0:1];
  assign reset_values[  0] = reset_values$000;
  assign reset_values[  1] = reset_values$001;

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
  // def update_last( reg_i=reg_i ):
  //           s.regs_next_last[ reg_i ].v = s.regs[ reg_i ]

  // logic for update_last()
  always @ (*) begin
    regs_next_last[reg_i] = regs[reg_i];
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
  // def update_last( reg_i=reg_i ):
  //           s.regs_next_last[ reg_i ].v = s.regs[ reg_i ]

  // logic for update_last()
  always @ (*) begin
    regs_next_last[reg_i] = regs[reg_i];
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


endmodule // RegisterFile_0x32d8e0d9c3795e02
`default_nettype wire

//-----------------------------------------------------------------------------
// RegisterFile_0x410c6f4c3e230ab0
//-----------------------------------------------------------------------------
// dtype: 2
// nregs: 2
// num_rd_ports: 2
// num_wr_ports: 1
// combinational_read_bypass: False
// combinational_dump_bypass: True
// dump_port: True
// reset_values: [<pymtl.model.signals.Wire object at 0x7fd692c50d50>, <pymtl.model.signals.Wire object at 0x7fd692c50650>]
// combinational_dump_read_bypass: True
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegisterFile_0x410c6f4c3e230ab0
(
  input  wire [   0:0] clk,
  input  wire [   1:0] dump_in$000,
  input  wire [   1:0] dump_in$001,
  output wire [   1:0] dump_out$000,
  output wire [   1:0] dump_out$001,
  input  wire [   0:0] dump_wr_en,
  input  wire [   0:0] rd_ports$000_addr,
  output wire [   1:0] rd_ports$000_data,
  input  wire [   0:0] rd_ports$001_addr,
  output wire [   1:0] rd_ports$001_data,
  input  wire [   0:0] reset,
  input  wire [   0:0] wr_ports$000_addr,
  input  wire [   0:0] wr_ports$000_call,
  input  wire [   1:0] wr_ports$000_data
);

  // wire declarations
  wire   [   1:0] reset_values$000;
  wire   [   1:0] reset_values$001;
  wire   [   1:0] regs_next_last$000;
  wire   [   1:0] regs_next_last$001;
  wire   [   1:0] regs_next$000;
  wire   [   1:0] regs_next$001;
  wire   [   1:0] regs$000;
  wire   [   1:0] regs$001;
  wire   [   1:0] regs_next_dump$000;
  wire   [   1:0] regs_next_dump$001;


  // localparam declarations
  localparam reg_i = 1;

  // signal connections
  assign dump_out$000     = regs_next_last$000;
  assign dump_out$001     = regs_next_last$001;
  assign reset_values$000 = 2'd0;
  assign reset_values$001 = 2'd0;

  // array declarations
  wire   [   1:0] dump_in[0:1];
  assign dump_in[  0] = dump_in$000;
  assign dump_in[  1] = dump_in$001;
  wire   [   0:0] rd_ports_addr[0:1];
  assign rd_ports_addr[  0] = rd_ports$000_addr;
  assign rd_ports_addr[  1] = rd_ports$001_addr;
  reg    [   1:0] rd_ports_data[0:1];
  assign rd_ports$000_data = rd_ports_data[  0];
  assign rd_ports$001_data = rd_ports_data[  1];
  reg    [   1:0] regs[0:1];
  assign regs$000 = regs[  0];
  assign regs$001 = regs[  1];
  reg    [   1:0] regs_next[0:1];
  assign regs_next$000 = regs_next[  0];
  assign regs_next$001 = regs_next[  1];
  reg    [   1:0] regs_next_dump[0:1];
  assign regs_next_dump$000 = regs_next_dump[  0];
  assign regs_next_dump$001 = regs_next_dump[  1];
  reg    [   1:0] regs_next_last[0:1];
  assign regs_next_last$000 = regs_next_last[  0];
  assign regs_next_last$001 = regs_next_last[  1];
  wire   [   1:0] reset_values[0:1];
  assign reset_values[  0] = reset_values$000;
  assign reset_values[  1] = reset_values$001;
  wire   [   0:0] wr_ports_addr[0:0];
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
  //           if s.dump_wr_en:
  //             s.rd_ports[ port ].data.v = s.dump_in[ reg_i ]
  //           else:
  //             s.rd_ports[ port ].data.v = s.regs[ s.rd_ports[ port ].addr ]

  // logic for handle_read()
  always @ (*) begin
    if (dump_wr_en) begin
      rd_ports_data[port] = dump_in[reg_i];
    end
    else begin
      rd_ports_data[port] = regs[rd_ports_addr[port]];
    end
  end

  // PYMTL SOURCE:
  //
  // @s.combinational
  // def handle_read( port=port ):
  //           if s.dump_wr_en:
  //             s.rd_ports[ port ].data.v = s.dump_in[ reg_i ]
  //           else:
  //             s.rd_ports[ port ].data.v = s.regs[ s.rd_ports[ port ].addr ]

  // logic for handle_read()
  always @ (*) begin
    if (dump_wr_en) begin
      rd_ports_data[port] = dump_in[reg_i];
    end
    else begin
      rd_ports_data[port] = regs[rd_ports_addr[port]];
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


endmodule // RegisterFile_0x410c6f4c3e230ab0
`default_nettype wire

//-----------------------------------------------------------------------------
// FreeList_0x35f64f2902ec6b0b
//-----------------------------------------------------------------------------
// nslots: 1
// num_alloc_ports: 1
// num_free_ports: 1
// combinational_bypass: False
// used_slots_initial: 0
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module FreeList_0x35f64f2902ec6b0b
(
  input  wire [   0:0] alloc_ports$000_call,
  output wire [   0:0] alloc_ports$000_index,
  output wire [   0:0] alloc_ports$000_rdy,
  input  wire [   0:0] clk,
  input  wire [   0:0] free_ports$000_call,
  input  wire [   0:0] free_ports$000_index,
  input  wire [   0:0] reset
);

  // wire declarations
  wire   [   0:0] free_size_next$000;
  wire   [   0:0] tail_next$000;
  wire   [   0:0] head_next$000;
  wire   [   0:0] alloc_size_next$000;
  wire   [   0:0] workaround_head_incs_inc_out$000;
  wire   [   0:0] workaround_tail_incs_inc_out$000;


  // register declarations
  reg    [   0:0] base__1;
  reg    [   0:0] base__3;
  reg    [   0:0] bypassed_size;
  reg    [   0:0] chead__3;
  reg    [   0:0] ctail__1;
  reg    [   0:0] head;
  reg    [   0:0] size;
  reg    [   0:0] tail;

  // localparam declarations
  localparam nslots = 1;
  localparam num_alloc_ports = 1;
  localparam num_free_ports = 1;
  localparam used_slots_initial = 0;

  // tail_incs$000 temporaries
  wire   [   0:0] tail_incs$000$reset;
  wire   [   0:0] tail_incs$000$clk;
  wire   [   0:0] tail_incs$000$inc_in_;
  wire   [   0:0] tail_incs$000$inc_out;

  WrapInc_0xad607aebe9fc4bb tail_incs$000
  (
    .reset   ( tail_incs$000$reset ),
    .clk     ( tail_incs$000$clk ),
    .inc_in_ ( tail_incs$000$inc_in_ ),
    .inc_out ( tail_incs$000$inc_out )
  );

  // head_incs$000 temporaries
  wire   [   0:0] head_incs$000$reset;
  wire   [   0:0] head_incs$000$clk;
  wire   [   0:0] head_incs$000$inc_in_;
  wire   [   0:0] head_incs$000$inc_out;

  WrapInc_0xad607aebe9fc4bb head_incs$000
  (
    .reset   ( head_incs$000$reset ),
    .clk     ( head_incs$000$clk ),
    .inc_in_ ( head_incs$000$inc_in_ ),
    .inc_out ( head_incs$000$inc_out )
  );

  // free temporaries
  wire   [   0:0] free$clk;
  wire   [   0:0] free$wr_ports$000_addr;
  wire   [   0:0] free$wr_ports$000_call;
  wire   [   0:0] free$wr_ports$000_data;
  wire   [   0:0] free$reset;
  wire   [   0:0] free$rd_ports$000_addr;
  wire   [   0:0] free$rd_ports$000_data;

  RegisterFile_0x38c806df9173c5a6 free
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
  reg    [   0:0] alloc_size_next[0:0];
  assign alloc_size_next$000 = alloc_size_next[  0];
  reg    [   0:0] free$rd_ports_addr[0:0];
  assign free$rd_ports$000_addr = free$rd_ports_addr[  0];
  reg    [   0:0] free$wr_ports_addr[0:0];
  assign free$wr_ports$000_addr = free$wr_ports_addr[  0];
  reg    [   0:0] free$wr_ports_call[0:0];
  assign free$wr_ports$000_call = free$wr_ports_call[  0];
  reg    [   0:0] free$wr_ports_data[0:0];
  assign free$wr_ports$000_data = free$wr_ports_data[  0];
  wire   [   0:0] free_ports_call[0:0];
  assign free_ports_call[  0] = free_ports$000_call;
  wire   [   0:0] free_ports_index[0:0];
  assign free_ports_index[  0] = free_ports$000_index;
  reg    [   0:0] free_size_next[0:0];
  assign free_size_next$000 = free_size_next[  0];
  reg    [   0:0] head_next[0:0];
  assign head_next$000 = head_next[  0];
  reg    [   0:0] tail_next[0:0];
  assign tail_next$000 = tail_next[  0];
  wire   [   0:0] workaround_head_incs_inc_out[0:0];
  assign workaround_head_incs_inc_out[  0] = workaround_head_incs_inc_out$000;
  wire   [   0:0] workaround_tail_incs_inc_out[0:0];
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


endmodule // FreeList_0x35f64f2902ec6b0b
`default_nettype wire

//-----------------------------------------------------------------------------
// WrapInc_0xad607aebe9fc4bb
//-----------------------------------------------------------------------------
// nbits: 1
// size: 1
// up: True
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module WrapInc_0xad607aebe9fc4bb
(
  input  wire [   0:0] clk,
  input  wire [   0:0] inc_in_,
  output reg  [   0:0] inc_out,
  input  wire [   0:0] reset
);

  // localparam declarations
  localparam size = 1;



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


endmodule // WrapInc_0xad607aebe9fc4bb
`default_nettype wire

//-----------------------------------------------------------------------------
// RegisterFile_0x38c806df9173c5a6
//-----------------------------------------------------------------------------
// dtype: 1
// nregs: 1
// num_rd_ports: 1
// num_wr_ports: 1
// combinational_read_bypass: False
// dump_port: False
// reset_values: [<pymtl.model.signals.Wire object at 0x7fd692c40210>]
// combinational_dump_read_bypass: False
// combinational_dump_bypass: False
// dump-vcd: False
// verilator-xinit: zeros
`default_nettype none
module RegisterFile_0x38c806df9173c5a6
(
  input  wire [   0:0] clk,
  input  wire [   0:0] rd_ports$000_addr,
  output wire [   0:0] rd_ports$000_data,
  input  wire [   0:0] reset,
  input  wire [   0:0] wr_ports$000_addr,
  input  wire [   0:0] wr_ports$000_call,
  input  wire [   0:0] wr_ports$000_data
);

  // wire declarations
  wire   [   0:0] reset_values$000;
  wire   [   0:0] regs_next_last$000;
  wire   [   0:0] regs_next$000;
  wire   [   0:0] regs$000;
  wire   [   0:0] regs_next_dump$000;


  // signal connections
  assign reset_values$000 = 1'd0;

  // array declarations
  wire   [   0:0] rd_ports_addr[0:0];
  assign rd_ports_addr[  0] = rd_ports$000_addr;
  reg    [   0:0] rd_ports_data[0:0];
  assign rd_ports$000_data = rd_ports_data[  0];
  reg    [   0:0] regs[0:0];
  assign regs$000 = regs[  0];
  reg    [   0:0] regs_next[0:0];
  assign regs_next$000 = regs_next[  0];
  reg    [   0:0] regs_next_dump[0:0];
  assign regs_next_dump$000 = regs_next_dump[  0];
  reg    [   0:0] regs_next_last[0:0];
  assign regs_next_last$000 = regs_next_last[  0];
  wire   [   0:0] reset_values[0:0];
  assign reset_values[  0] = reset_values$000;
  wire   [   0:0] wr_ports_addr[0:0];
  assign wr_ports_addr[  0] = wr_ports$000_addr;
  wire   [   0:0] wr_ports_call[0:0];
  assign wr_ports_call[  0] = wr_ports$000_call;
  wire   [   0:0] wr_ports_data[0:0];
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


endmodule // RegisterFile_0x38c806df9173c5a6
`default_nettype wire

