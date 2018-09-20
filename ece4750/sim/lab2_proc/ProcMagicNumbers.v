`ifndef LAB2_PROC_MAGIN_NUMS
`define LAB2_PROC_MAGIN_NUMS

// Generic Parameters -- yes or no

localparam n = 1'd0;
localparam y = 1'd1;

// Register specifiers

localparam rx = 5'bx;   // don't care
localparam r0 = 5'd0;   // zero
localparam rL = 5'd31;  // for jal

// Branch type

localparam br_x     = 3'bx; // Don't care
localparam br_na    = 3'd0; // No branch
localparam br_beq   = 3'd1; // beq
localparam br_bne   = 3'd2; // bne
localparam br_blt   = 3'd3; // blt
localparam br_bge   = 3'd4; // bge
localparam br_bltu   = 3'd5; // bltu
localparam br_bgeu   = 3'd6; // bgeu



// Jump type
localparam jmp_x =2'bx;
localparam jmp_na =2'd0;
localparam jmp_X = 2'd2;
localparam jmp_D = 2'd3;

// Operand 1 Mux Select

localparam am_x     = 1'bx; // Don't care
localparam am_pc    = 1'd0; // Use data from register file
localparam am_rf    = 1'd1; // Use PC

// Operand 2 Mux Select

localparam bm_x     = 2'bx; // Don't care
localparam bm_rf    = 2'd0; // Use data from register file
localparam bm_imm   = 2'd1; // Use sign-extended immediate
localparam bm_csr   = 2'd2; // Use from mngr data

// ALU Function

typedef enum logic [3:0] {
  ALU_X = 4'dx,
  ALU_ADD = 4'd0,
  ALU_SUB = 4'd1,
  ALU_AND = 4'd2,
  ALU_XOR = 4'd3,
  ALU_OR = 4'd4,
  ALU_SLT = 4'd5,
  ALU_SLTU = 4'd6,
  ALU_SRA = 4'd7,
  ALU_SRL = 4'd8,
  ALU_SLL = 4'd9,

  ALU_LUI = 4'd10,
  ALU_CP0 = 4'd11,
  ALU_CP1 = 4'd12,
  ALU_AUIPC = 4'd13
  // DO NOT DEFINE 14
} alu_op_t;

// Immediate Type
localparam imm_x    = 3'bx;
localparam imm_i    = 3'd0;
localparam imm_s    = 3'd1;
localparam imm_b    = 3'd2;
localparam imm_u    = 3'd3;
localparam imm_j    = 3'd4;

// Memory Request Type

localparam nr       = 2'd0; // No request
localparam ld       = 2'd1; // Load
localparam st       = 2'd2; // Store

// Writeback Mux Select

localparam wm_x     = 1'bx; // Don't care
localparam wm_a     = 1'b0; // Use ALU output
localparam wm_m     = 1'b1; // Use data memory response-

// Execute Result Mux Select

localparam xm_x     = 2'dx; // Don't care
localparam xm_f     = 2'd0; // Use +4 unit output
localparam xm_a     = 2'd1; // Use ALU output
localparam xm_m     = 2'd2; // Use multiplier output

// Bypass Select
localparam b_N      = 2'd0;
localparam b_X      = 2'd1;
localparam b_M      = 2'd2;
localparam b_W      = 2'd3;

`endif
