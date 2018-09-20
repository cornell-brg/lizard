//========================================================================
// Datapath Components for 5-Stage Pipelined Processor
//========================================================================

`ifndef LAB2_PROC_DPATH_COMPONENTS_V
`define LAB2_PROC_DPATH_COMPONENTS_V

`include "lab2_proc/TinyRV2InstVRTL.v"

`include "lab2_proc/ProcMagicNumbers.v"

//------------------------------------------------------------------------
// Generate intermediate (imm) based on type
//------------------------------------------------------------------------

module lab2_proc_ImmGenVRTL
(
  input  logic [ 2:0] imm_type,
  input  logic [31:0] inst,
  output logic [31:0] imm
);

  always_comb begin
    case ( imm_type )
      imm_i: // I-type
        imm = { {21{inst[31]}}, inst[30:25], inst[24:21], inst[20] };

      imm_b: // B-type
        imm = { {20{inst[31]}}, inst[7], inst[30:25], inst[11:8], 1'b0 };

      //''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''
      // Add more immediate types
      //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
      imm_s: // S-type
        imm = { {21{inst[31]}}, inst[30:25], inst[11:7]};

      imm_j: // J-type
        imm = { {12{inst[31]}}, inst[19:12], inst[20], inst[30:21], 1'b0 };

      imm_u: // U-type
        imm = { inst[31:12], 12'b0 };

      default:
        imm = 32'bx;

    endcase
  end

endmodule

//------------------------------------------------------------------------
// ALU
//------------------------------------------------------------------------

`include "vc/arithmetic.v"

module lab2_proc_AluVRTL
(
  input  logic [31:0] in0,
  input  logic [31:0] in1,
  input  logic [ 3:0] fn,
  output logic [31:0] out,
  output logic        ops_eq,
  output logic        ops_lt,
  output logic        ops_ltu
);

  logic [31:0] add_res = in0 + in1;

  always_comb begin

    case ( fn )
      ALU_ADD : out = add_res;                                // ADD
      ALU_SUB : out = in0 - in1;                                // SUB

      ALU_AND : out = in0 & in1;                                // AND
      ALU_OR  : out = in0 | in1;                                // OR
      ALU_XOR : out = in0 ^ in1;                                // XOR

      ALU_SLTU : out = { 31'b0, in0 < in1 };
      ALU_SLT : out = { 31'b0, $signed(in0) < $signed(in1) };

      ALU_SRA : out = $signed(in0) >>> in1[4:0];
      ALU_SRL : out = in0 >> in1[4:0];
      ALU_SLL : out = in0 << in1[4:0];

      ALU_LUI : out = in1;

      ALU_AUIPC : out = in0 + in1;

      ALU_CP0 : out = in0;                                      // CP OP0
      ALU_CP1 : out = in1;                                      // CP OP1

      //''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''
      // Add more alu function
      //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

      default : out = 32'b0;
    endcase

  end

  // Calculate equality, zero, negative flags
  assign ops_ltu = in0 < in1;
  assign ops_lt = $signed(in0) < $signed(in1);
  assign ops_eq = (in0 == in1);


  //''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''
  // Add more alu function
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

endmodule

// selects branch from execute stage
module lab2_proc_br_jmp_selector
(
    input  logic [31:0] in0,
    input  logic [31:0] in1,
    input  logic sel,
    output logic [31:0] out
);
  assign out = sel ? (in1 & 32'hfffffffe) : in0;

endmodule

`endif
