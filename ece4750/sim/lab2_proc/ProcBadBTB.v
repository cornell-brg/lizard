`ifndef LAB2_PROC_BTB_V
`define LAB2_PROC_BTB_V

`include "vc/trace.v"
`include "lab2_proc/TinyRV2InstVRTL.v"
`include "lab2_proc/ProcMagicNumbers.v"
`include "lab2_proc/ProcDesignControl.v"

localparam  PROC_BTB_WRITE_TAKEN     = 2'd0;
localparam  PROC_BTB_WRITE_NOT_TAKEN = 2'd1;
localparam  PROC_BTB_WRITE_NONE      = 2'd2;

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

// Loop forever!!
assign target_pc = fetch_pc;
// Always hit
assign hit = 1'b1;

endmodule
`endif
