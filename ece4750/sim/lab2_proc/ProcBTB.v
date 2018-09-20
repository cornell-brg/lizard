`ifndef LAB2_PROC_BTB_V
`define LAB2_PROC_BTB_V

`include "vc/trace.v"
`include "lab2_proc/TinyRV2InstVRTL.v"
`include "lab2_proc/ProcMagicNumbers.v"
`include "lab2_proc/ProcDesignControl.v"

localparam  PROC_BTB_WRITE_TAKEN     = 2'd0;
localparam  PROC_BTB_WRITE_NOT_TAKEN = 2'd1;
localparam  PROC_BTB_WRITE_NONE      = 2'd2;

localparam zshift = 2;
localparam btb_size = 8;
localparam entry_size = 32 - zshift;
localparam index_size = $clog2(btb_size);

typedef struct packed {
  logic        val;
  logic [entry_size - 1:0] key;
  logic [entry_size - 1:0] value;
} BTBEntry;

typedef struct packed {
  logic        val;
  logic [index_size - 1:0] index;
} BTBIndex;

function [entry_size - 1:0] addr_in;
  input [31:0] a;
  begin
    addr_in = a[31:zshift];
  end
endfunction

function [31:0] addr_out;
  input [entry_size - 1:0] a;
  begin
    addr_out = {a, {zshift{1'b0}}};
  end
endfunction


module lab2_proc_BTBHitHelper (
    input  logic    [31:0] pc,
    input  BTBEntry        btb [btb_size - 1:0],
    output BTBIndex        hit_index
);
BTBIndex hit_helper [btb_size:0];
logic [entry_size-1:0] in_pc;
assign in_pc = addr_in(pc);
genvar i;
generate
for (i = 0; i < btb_size; i++) begin: HIT_HELPER
  assign hit_helper[i].val = (in_pc == btb[i].key && btb[i].val ? 1'b1 : (i == 0 ? 1'b0 : hit_helper[i-1].val));
  assign hit_helper[i].index = (in_pc == btb[i].key && btb[i].val ? i[index_size - 1:0] : (i == 0 ? {index_size{1'bx}} : hit_helper[i-1].index));
end
endgenerate
assign hit_index = hit_helper[btb_size - 1];

endmodule

module lab2_proc_ProcBTB (
  input  logic       clk,
  input  logic       reset,
  input  logic [31:0] fetch_pc,
  output logic [31:0] target_pc,
  output logic        hit,
  input  logic [31:0] write_pc,
  input  logic [31:0] jump_pc,
  input  logic [1:0]  write_config
);


BTBEntry btb[btb_size - 1:0];
BTBIndex read_idx;
lab2_proc_BTBHitHelper read_index_helper (
  .pc         (fetch_pc),
  .btb        (btb),
  .hit_index  (read_idx)
);

BTBIndex overwrite_index;
lab2_proc_BTBHitHelper overwrite_index_helper (
  .pc         (write_pc),
  .btb        (btb),
  .hit_index  (overwrite_index)
);

assign hit = read_idx.val;
assign target_pc = addr_out(btb[read_idx.index].value);

logic [index_size - 1:0] replace_idx;
logic [index_size - 1:0] write_idx;

logic [index_size - 1:0] replace_helper [btb_size];
genvar i;
generate
for (i = 0; i < btb_size; i++) begin : REPLACE_HELPER
  assign replace_helper[i] = !btb[i].val ? i[index_size-1:0] : (i == 0 ? replace_idx : replace_helper[i-1]);
end
endgenerate

assign write_idx = overwrite_index.val ? overwrite_index.index : replace_helper[btb_size - 1];

generate
for (i = 0; i < btb_size; i++) begin : RESET_BLOCKS
  always_ff @( posedge clk ) begin
    if (reset) begin
      btb[i].val <= 1'b0;
    end
  end
end
endgenerate

always_ff @( posedge clk ) begin
  if (reset) begin
    replace_idx <= {index_size{1'b0}};
  end else begin
    replace_idx <= replace_idx + {{(index_size-1){1'b0}}, 1'b1};
    if (write_config == PROC_BTB_WRITE_TAKEN) begin
      btb[write_idx].val   <= 1'b1;
      btb[write_idx].key   <= addr_in(write_pc);
      btb[write_idx].value <= addr_in(jump_pc);
    end else if (write_config == PROC_BTB_WRITE_NOT_TAKEN) begin
      if (overwrite_index.val) btb[overwrite_index.index].val = 1'b0;
    end
  end
end



endmodule
`endif
