//=========================================================================
// 5-Stage Stalling Pipelined Processor Control
//=========================================================================

`ifndef LAB2_PROC_PIPELINED_PROC_CTRL_V
`define LAB2_PROC_PIPELINED_PROC_CTRL_V

`include "vc/trace.v"
`include "lab2_proc/TinyRV2InstVRTL.v"
`include "lab2_proc/ProcMagicNumbers.v"
`include "lab2_proc/ProcDesignControl.v"
`include "lab2_proc/ProcBTB.v"

module lab2_proc_ProcCtrlVRTL
#(
  parameter p_type = `PROC_DESIGN_STALLING,
  parameter p_use_btb = `PROC_DESIGN_NO_BTB
)(
  input  logic        clk,
  input  logic        reset,

  // Instruction Memory Port

  output logic        imemreq_val,
  input  logic        imemreq_rdy,

  input  logic        imemresp_val,
  output logic        imemresp_rdy,

  output logic        imemresp_drop,

  // Data Memory Port

  output logic        dmemreq_val,
  input  logic        dmemreq_rdy,

  input  logic        dmemresp_val,
  output logic        dmemresp_rdy,

  // mngr communication portLAB2_PROC_

  input  logic        mngr2proc_val,
  output logic        mngr2proc_rdy,

  output logic        proc2mngr_val,
  input  logic        proc2mngr_rdy,

  // control signals (ctrl->dpath)

  output logic        reg_en_F,
  output logic [2:0]  pc_sel_F,
  output logic        btb_sel_F,

  output logic        reg_en_D,
  output logic        op1_sel_D,
  output logic [1:0]  op2_sel_D,
  output logic [1:0]  csrr_sel_D,
  output logic [2:0]  imm_type_D,
  output logic [1:0]  op1_bypass_sel_D,
  output logic [1:0]  op2_bypass_sel_D,

  output logic        reg_en_X,
  output logic [3:0]  alu_fn_X,
  output logic [1:0]  btb_write_config_X,
  output logic [1:0]  dmemreq_type_X,

  output logic        reg_en_M,
  output logic        wb_result_sel_M,

  output logic        reg_en_W,
  output logic [4:0]  rf_waddr_W,
  output logic        rf_wen_W,

  output logic        imul_req_val_D,
  output logic        imul_resp_rdy_X,

  output logic [1:0]  ex_result_sel_X,
  output logic        br_jmp_sel_X,


  // status signals (dpath->ctrl)

  input  logic        btb_raw_hit_F,
  input  logic [31:0] inst_D,
  input  logic        btb_correct_D,
  input  logic        btb_correct_X,
  input  logic        br_cond_eq_X,
  input  logic        br_cond_lt_X,
  input  logic        br_cond_ltu_X,

  input  logic        imul_req_rdy_D,
  input  logic        imul_resp_val_X,

  output logic        stats_en_wen_W,

  output logic        commit_inst

);

  logic bypassing;
  assign bypassing = (p_type == `PROC_DESIGN_BYPASSED);

  //----------------------------------------------------------------------
  // Notes
  //----------------------------------------------------------------------
  // We follow this principle to organize code for each pipeline stage in
  // the control unit.  Register enable logics should always at the
  // beginning. It followed by pipeline registers. Then logic that is not
  // dependent on stall or squash signals. Then logic that is dependent
  // on stall or squash signals. At the end there should be signals meant
  // to be passed to the next stage in the pipeline.

  //----------------------------------------------------------------------
  // Valid, stall, and squash signals
  // ----------------------------------------------------------------------
  // We use valid signal to indicate if the instruction is valid.  An
  // instruction can become invalid because of being squashed or
  // stalled. Notice that invalid instructions are microarchitectural
  // events, they are different from archtectural no-ops. We must be
  // careful about control signals that might change the state of the
  // processor. We should always AND outgoing control signals with valid
  // signal.

  logic val_F;
  logic val_D;
  logic val_X;
  logic val_M;
  logic val_W;

  // Managing the stall and squash signals is one of the most important,
  // yet also one of the most complex, aspects of designing a pipelined
  // processor. We will carefully use four signals per stage to manage
  // stalling and squashing: ostall_A, osquash_A, stall_A, and squash_A.
  //
  // We denote the stall signals _originating_ from stage A as
  // ostall_A. For example, if stage A can stall due to a pipeline
  // harzard, then ostall_A would need to factor in the stalling
  // condition for this pipeline harzard.

  logic ostall_F;  // can ostall due to imemresp_val
  logic ostall_D;  // can ostall due to mngr2proc_val or other hazards
  logic ostall_X;  // can ostall due to dmemreq_rdy
  logic ostall_M;  // can ostall due to dmemresp_val
  logic ostall_W;  // can ostall due to proc2mngr_rdy

  // The stall_A signal should be used to indicate when stage A is indeed
  // stalling. stall_A will be a function of ostall_A and all the ostall
  // signals of stages in front of it in the pipeline.

  logic stall_F;
  logic stall_D;
  logic stall_X;
  logic stall_M;
  logic stall_W;

  // We denote the squash signals _originating_ from stage A as
  // osquash_A. For example, if stage A needs to squash the stages behind
  // A in the pipeline, then osquash_A would need to factor in this
  // squash condition.

  logic osquash_D; // can osquash due to unconditional jumps
  logic osquash_X; // can osquash due to taken branches

  // The squash_A signal should be used to indicate when stage A is being
  // squashed. squash_A will _not_ be a function of osquash_A, since
  // osquash_A means to squash the stages _behind_ A in the pipeline, but
  // not to squash A itself.

  logic squash_F;
  logic squash_D;

  //----------------------------------------------------------------------
  // F stage
  //----------------------------------------------------------------------

  // Register enable logic

  assign reg_en_F = !stall_F || squash_F;

  // Pipeline registers

  always_ff @( posedge clk ) begin
    if ( reset )
      val_F <= 1'b0;
    else if ( reg_en_F )
      val_F <= 1'b1;
  end

  // forward declaration for PC sel
  localparam  PC_SHOULD_NOT_HAVE_BRANCHED = 2'd0;
  localparam  PC_BRANCHED_TO_WRONG_INST   = 2'd1;
  localparam  PC_BRANCHED_CORRECTLY       = 2'd2;
  logic [1:0] pc_redirect_X;
  logic [1:0] pc_redirect_D;
  logic btb_hit_F;

  // Allows easy BTB disabling with p_use_btb = 0 because then it will never
  // be a hit
  assign btb_hit_F = p_use_btb && btb_raw_hit_F;
  // If it was a hit, select from BTB, otherwise don't
  assign btb_sel_F = btb_hit_F;

  // PC select logic
  always_comb begin
    if      ( pc_redirect_X == PC_SHOULD_NOT_HAVE_BRANCHED) pc_sel_F = 3'd3; // squash and go back to PC_X + 4
    else if ( pc_redirect_X == PC_BRANCHED_TO_WRONG_INST)   pc_sel_F = 3'd1; // squash and use branch target from X
    // If decoded jump inst, note this has lower priority than in X stage
    else if ( pc_redirect_D == PC_SHOULD_NOT_HAVE_BRANCHED) pc_sel_F = 3'd4; // squash and go back to PC_D + 4
    else if ( pc_redirect_D == PC_BRANCHED_TO_WRONG_INST)   pc_sel_F = 3'd2; // squash and use branch target from D
    else                                                    pc_sel_F = 3'd0; // use BTB guess / pc + 4
  end

  // ostall due to the imem response not valid.

  assign ostall_F = val_F && !imemresp_val;

  // stall and squash in F

  assign stall_F  = val_F && ( ostall_F  || ostall_D || ostall_X || ostall_M || ostall_W );
  assign squash_F = val_F && ( osquash_D || osquash_X );

  // We drop the mem response when we are getting squashed

  assign imemresp_drop = squash_F;

  // imem is very special. Actually imem requests are sent before the F
  // stage. Note that we need to factor in reset to the imemreq_val
  // signal because we don't want to send out imem request when we are
  // resetting.

  assign imemreq_val  = ( !stall_F || squash_F ) && !reset;
  assign imemresp_rdy = !stall_F || squash_F;

  // Valid signal for the next stage (stage D)

  logic  next_val_F;
  assign next_val_F = val_F && !stall_F && !squash_F;

  //----------------------------------------------------------------------
  // D stage
  //----------------------------------------------------------------------

  // Register enable logic

  assign reg_en_D = !stall_D || squash_D;

  // Pipline registers
  logic       btb_hit_D;

  always_ff @( posedge clk ) begin
    if ( reset ) begin
      val_D <= 1'b0;
      btb_hit_D <= 1'b0;
    end else if ( reg_en_D ) begin
      val_D <= next_val_F;
      btb_hit_D <= btb_hit_F;
    end
  end

  // Parse instruction fields

  logic   [4:0] inst_rd_D;
  logic   [4:0] inst_rs1_D;
  logic   [4:0] inst_rs2_D;
  logic   [11:0] inst_csr_D;

  rv2isa_InstUnpack inst_unpack
  (
    .inst     (inst_D),
    .opcode   (),
    .rd       (inst_rd_D),
    .rs1      (inst_rs1_D),
    .rs2      (inst_rs2_D),
    .funct3   (),
    .funct7   (),
    .csr      (inst_csr_D)
  );

  // Instruction Decode

  logic       inst_val_D;
  logic [2:0] br_type_D;
  logic [1:0] jmp_type_D;
  logic       rs1_en_D;
  logic       rs2_en_D;
  logic [3:0] alu_fn_D;
  logic [1:0] dmemreq_type_D;
  logic       is_lw_D;
  logic       wb_result_sel_D;
  logic       rf_wen_pending_D;
  logic       csrr_D;
  logic       csrw_D;
  logic       proc2mngr_val_D;
  logic       mngr2proc_rdy_D;
  logic       stats_en_wen_D;
  logic [1:0] ex_result_sel_D;
  logic       is_mul_D;

  logic        is_lw_X;

  task cs
  (
    input logic       cs_inst_val,
    input logic [2:0] cs_br_type,
    input logic [1:0] cs_jmp_type,
    input logic [2:0] cs_imm_type,
    input logic       cs_rs1_en,
    input logic       cs_op1_sel,
    input logic [1:0] cs_op2_sel,
    input logic       cs_rs2_en,
    input logic [3:0] cs_alu_fn,
    input logic [1:0] cs_dmemreq_type,
    input logic       cs_wb_result_sel,
    input logic       cs_rf_wen_pending,
    input logic       cs_csrr,
    input logic       cs_csrw,
    input logic [1:0] ex_result_sel
  );
  begin
    inst_val_D            = cs_inst_val;
    br_type_D             = cs_br_type;
    jmp_type_D            = cs_jmp_type;
    imm_type_D            = cs_imm_type;
    rs1_en_D              = cs_rs1_en;
    op1_sel_D             = cs_op1_sel;
    op2_sel_D             = cs_op2_sel;
    rs2_en_D              = cs_rs2_en;
    alu_fn_D              = cs_alu_fn;
    dmemreq_type_D        = cs_dmemreq_type;
    is_lw_D               = cs_dmemreq_type == ld;
    wb_result_sel_D       = cs_wb_result_sel;
    rf_wen_pending_D      = cs_rf_wen_pending;
    csrr_D                = cs_csrr;
    csrw_D                = cs_csrw;
    ex_result_sel_D       = ex_result_sel;
    is_mul_D              = ex_result_sel == xm_m;
  end
  endtask

  // Control signals table
  always_comb begin

    casez ( inst_D )
      //                           br      jmp    imm  rs1  op1    op2    rs2 alu        dmm wbmux rf            exmux
      //                       val type   stage   type  en  muxsel muxsel  en fn         typ sel   wen csrr csrw sel
      `RV2ISA_INST_NOP     :cs( y, br_na, jmp_na, imm_x, n, am_x,  bm_x,   n, ALU_X,     nr, wm_a, n,  n,   n,    xm_a   );

      // RR
      `RV2ISA_INST_ADD     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_ADD,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SUB     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SUB,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_XOR     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_XOR,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_AND     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_AND,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_OR      :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_OR,    nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SLT     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SLT,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SLTU    :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SLTU,  nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SRA     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SRA,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SRL     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SRL,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SLL     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SLL,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_MUL     :cs( y, br_na, jmp_na, imm_x, y, am_rf, bm_rf,  y, ALU_SLL,   nr, wm_a, y,  n,   n,    xm_m   );

      // RIMM
      `RV2ISA_INST_ADDI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_ADD,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_ANDI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_AND,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_ORI     :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_OR,    nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_XORI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_XOR,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SLTI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_SLT,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SLTIU   :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_SLTU,  nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SLLI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_SLL,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SRLI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_SRL,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SRAI    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_SRA,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_LUI     :cs( y, br_na, jmp_na, imm_u, y, am_rf, bm_imm, n, ALU_LUI,   nr, wm_a, y,  n,   n,    xm_a   );
      `RV2ISA_INST_AUIPC   :cs( y, br_na, jmp_na, imm_u, y, am_pc, bm_imm, n, ALU_AUIPC, nr, wm_a, y,  n,   n,    xm_a   );

      // MEM
      `RV2ISA_INST_LW      :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_imm, n, ALU_ADD,   ld, wm_m, y,  n,   n,    xm_a   );
      `RV2ISA_INST_SW      :cs( y, br_na, jmp_na, imm_s, y, am_rf, bm_imm, y, ALU_ADD,   st, wm_x, n,  n,   n,    xm_a   );

      // BRANCH
      `RV2ISA_INST_BNE     :cs( y, br_bne, jmp_na, imm_b, y, am_rf, bm_rf,  y, ALU_X,    nr, wm_a, n,  n,   n,    xm_a   );
      `RV2ISA_INST_BEQ     :cs( y, br_beq, jmp_na, imm_b, y, am_rf, bm_rf,  y, ALU_X,    nr, wm_a, n,  n,   n,    xm_a   );
      `RV2ISA_INST_BLT     :cs( y, br_blt, jmp_na, imm_b, y, am_rf, bm_rf,  y, ALU_X,    nr, wm_a, n,  n,   n,    xm_a   );
      `RV2ISA_INST_BGE     :cs( y, br_bge, jmp_na, imm_b, y, am_rf, bm_rf,  y, ALU_X,    nr, wm_a, n,  n,   n,    xm_a   );
      `RV2ISA_INST_BLTU    :cs( y, br_bltu,jmp_na, imm_b, y, am_rf, bm_rf,  y, ALU_X,    nr, wm_a, n,  n,   n,    xm_a   );
      `RV2ISA_INST_BGEU    :cs( y, br_bgeu,jmp_na, imm_b, y, am_rf, bm_rf,  y, ALU_X,    nr, wm_a, n,  n,   n,    xm_a   );

      // JUMP
      `RV2ISA_INST_JAL     :cs( y, br_na,  jmp_D,  imm_j, n, am_x,  bm_x,   n, ALU_X,    nr, wm_a, y,  n,   n,    xm_f   );
      `RV2ISA_INST_JALR    :cs( y, br_na,  jmp_X,  imm_i, y, am_rf, bm_imm, n, ALU_ADD,  nr, wm_a, y,  n,   n,    xm_f   );

      // Test intructions
      `RV2ISA_INST_CSRR    :cs( y, br_na, jmp_na, imm_i, n, am_rf, bm_csr, n, ALU_CP1,   nr, wm_a, y,  y,   n,    xm_a   );
      `RV2ISA_INST_CSRW    :cs( y, br_na, jmp_na, imm_i, y, am_rf, bm_rf,  n, ALU_CP0,   nr, wm_a, n,  n,   y,    xm_a   );

      default              :cs( n, br_x,  jmp_na, imm_x, n, am_x, bm_x,    n, ALU_X,     nr, wm_x, n,  n,   n,    xm_x   );

    endcase
  end // always_comb

  logic [4:0] rf_waddr_D;
  assign rf_waddr_D = inst_rd_D;

  // Validate JAL BTB predictions

  always_comb begin
    if (val_D) begin
      if (btb_hit_D) begin
        if (jmp_type_D == jmp_D) begin
          if (btb_correct_D) pc_redirect_D = PC_BRANCHED_CORRECTLY;
          else pc_redirect_D = PC_BRANCHED_TO_WRONG_INST;
        end else pc_redirect_D = PC_BRANCHED_CORRECTLY;
      end else begin
        if (jmp_type_D == jmp_D) pc_redirect_D = PC_BRANCHED_TO_WRONG_INST;
        else pc_redirect_D = PC_BRANCHED_CORRECTLY;
      end
    end else pc_redirect_D = PC_BRANCHED_CORRECTLY;
  end

  // csrr and csrw logic

  always_comb begin
    proc2mngr_val_D  = 1'b0;
    mngr2proc_rdy_D  = 1'b0;
    csrr_sel_D       = 2'h0;
    stats_en_wen_D   = 1'b0;

    if ( csrw_D && inst_csr_D == `RV2ISA_CPR_PROC2MNGR )
      proc2mngr_val_D    = 1'b1;
    if ( csrr_D && inst_csr_D == `RV2ISA_CPR_MNGR2PROC )
      mngr2proc_rdy_D  = 1'b1;
    if ( csrw_D && inst_csr_D == `RV2ISA_CPR_STATS_EN )
      stats_en_wen_D  = 1'b1;
    if ( csrr_D && inst_csr_D == `RV2ISA_CPR_NUMCORES )
      csrr_sel_D       = 2'h1;
    if ( csrr_D && inst_csr_D == `RV2ISA_CPR_COREID )
      csrr_sel_D       = 2'h2;
  end

  // mngr2proc_rdy signal for csrr instruction

  assign mngr2proc_rdy  = val_D && !stall_D && mngr2proc_rdy_D && !squash_D;

  logic  ostall_mngr2proc_D;
  assign ostall_mngr2proc_D = val_D && mngr2proc_rdy_D && !mngr2proc_val;

  // ostall if write address in X matches rs1 in D

  logic waddr_X_rs1_D;
  assign waddr_X_rs1_D
    = rs1_en_D && val_X && rf_wen_pending_X
      && ( inst_rs1_D == rf_waddr_X ) && ( rf_waddr_X != 5'd0 );
  logic  ostall_waddr_X_rs1_D;
  assign ostall_waddr_X_rs1_D = !bypassing && waddr_X_rs1_D;
  logic  bypass_waddr_X_rs1_D;
  assign bypass_waddr_X_rs1_D =  bypassing && waddr_X_rs1_D;

  // ostall if write address in X matches rs1 in D and X is a LW
  logic ostall_load_use_X_rs1_D;
  assign ostall_load_use_X_rs1_D
    = rs1_en_D && val_X && rf_wen_pending_X
      && ( inst_rs1_D == rf_waddr_X ) && ( rf_waddr_X != 5'd0 )
      && ( is_lw_X );

  // ostall if write address in M matches rs1 in D

  logic  waddr_M_rs1_D;
  assign waddr_M_rs1_D
    = rs1_en_D && val_M && rf_wen_pending_M
      && ( inst_rs1_D == rf_waddr_M ) && ( rf_waddr_M != 5'd0 );
  logic  ostall_waddr_M_rs1_D;
  assign ostall_waddr_M_rs1_D = !bypassing && waddr_M_rs1_D;
  logic  bypass_waddr_M_rs1_D;
  assign bypass_waddr_M_rs1_D =  bypassing && waddr_M_rs1_D;

  // ostall if write address in W matches rs1 in D

  logic  waddr_W_rs1_D;
  assign waddr_W_rs1_D
    = rs1_en_D && val_W && rf_wen_pending_W
      && ( inst_rs1_D == rf_waddr_W ) && ( rf_waddr_W != 5'd0 );
  logic  ostall_waddr_W_rs1_D;
  assign ostall_waddr_W_rs1_D = !bypassing && waddr_W_rs1_D;
  logic  bypass_waddr_W_rs1_D;
  assign bypass_waddr_W_rs1_D =  bypassing && waddr_W_rs1_D;

  // ostall if write address in X matches rs2 in D

  logic waddr_X_rs2_D;
  assign waddr_X_rs2_D
    = rs2_en_D && val_X && rf_wen_pending_X
      && ( inst_rs2_D == rf_waddr_X ) && ( rf_waddr_X != 5'd0 );
  logic  ostall_waddr_X_rs2_D;
  assign ostall_waddr_X_rs2_D = !bypassing && waddr_X_rs2_D;
  logic  bypass_waddr_X_rs2_D;
  assign bypass_waddr_X_rs2_D =  bypassing && waddr_X_rs2_D;

  // ostall if write address in X matches rs2 in D and X is a LW
  logic ostall_load_use_X_rs2_D;
  assign ostall_load_use_X_rs2_D
    = rs2_en_D && val_X && rf_wen_pending_X
      && ( inst_rs2_D == rf_waddr_X ) && ( rf_waddr_X != 5'd0 )
      && ( is_lw_X );

  // ostall if write address in M matches rs2 in D

  logic  waddr_M_rs2_D;
  assign waddr_M_rs2_D
    = rs2_en_D && val_M && rf_wen_pending_M
      && ( inst_rs2_D == rf_waddr_M ) && ( rf_waddr_M != 5'd0 );
  logic  ostall_waddr_M_rs2_D;
  assign ostall_waddr_M_rs2_D = !bypassing && waddr_M_rs2_D;
  logic  bypass_waddr_M_rs2_D;
  assign bypass_waddr_M_rs2_D =  bypassing && waddr_M_rs2_D;

  // ostall if write address in W matches rs2 in D

  logic  waddr_W_rs2_D;
  assign waddr_W_rs2_D
    = rs2_en_D && val_W && rf_wen_pending_W
      && ( inst_rs2_D == rf_waddr_W ) && ( rf_waddr_W != 5'd0 );
  logic  ostall_waddr_W_rs2_D;
  assign ostall_waddr_W_rs2_D = !bypassing && waddr_W_rs2_D;
  logic  bypass_waddr_W_rs2_D;
  assign bypass_waddr_W_rs2_D =  bypassing && waddr_W_rs2_D;

  // Put together ostall signal due to hazards

  logic  ostall_hazard_D;
  assign ostall_hazard_D =
      ostall_waddr_X_rs1_D || ostall_waddr_M_rs1_D || ostall_waddr_W_rs1_D ||
      ostall_waddr_X_rs2_D || ostall_waddr_M_rs2_D || ostall_waddr_W_rs2_D ||
      ostall_load_use_X_rs1_D || ostall_load_use_X_rs2_D;

  // ostall if instruction in decode is a multiply, but the multiplier isn't ready

  logic  ostall_mul_rdy_D;
  assign ostall_mul_rdy_D = val_D && is_mul_D && !imul_req_rdy_D;

  // Final ostall signal

  assign ostall_D = val_D && ( ostall_mngr2proc_D || ostall_hazard_D || ostall_mul_rdy_D);

  // osquash due to jump instruction in D stage (not implemented yet)

  assign osquash_D = val_D && !stall_D && (pc_redirect_D != PC_BRANCHED_CORRECTLY); // If we are redirecting PC, then squash

  // stall and squash in D

  assign stall_D  = val_D && ( ostall_D || ostall_X || ostall_M || ostall_W );
  assign squash_D = val_D && osquash_X;

  assign op1_bypass_sel_D = bypass_waddr_X_rs1_D ? b_X : (bypass_waddr_M_rs1_D ? b_M : (bypass_waddr_W_rs1_D ? b_W : b_N));
  assign op2_bypass_sel_D = bypass_waddr_X_rs2_D ? b_X : (bypass_waddr_M_rs2_D ? b_M : (bypass_waddr_W_rs2_D ? b_W : b_N));

  // Valid signal for the next stage

  logic  next_val_D;
  assign next_val_D = val_D && !stall_D && !squash_D;

  // Multiplier valid logic
  assign imul_req_val_D = val_D && !stall_D && !squash_D && is_mul_D;

  //----------------------------------------------------------------------
  // X stage
  //----------------------------------------------------------------------

  // Register enable logic

  assign reg_en_X = !stall_X;

  logic [31:0] inst_X;
  logic        wb_result_sel_X;
  logic        rf_wen_pending_X;
  logic [4:0]  rf_waddr_X;
  logic        proc2mngr_val_X;
  logic        stats_en_wen_X;
  logic [2:0]  br_type_X;
  logic [1:0]  jmp_type_X;
  logic        btb_hit_X;
  logic        is_mul_X;

  // Pipeline registers

  always_ff @( posedge clk )
    if (reset) begin
      val_X           <= 1'b0;
      stats_en_wen_X  <= 1'b0;
    end else if (reg_en_X) begin
      val_X           <= next_val_D;
      rf_wen_pending_X<= rf_wen_pending_D;
      inst_X          <= inst_D;
      alu_fn_X        <= alu_fn_D;
      rf_waddr_X      <= rf_waddr_D;
      proc2mngr_val_X <= proc2mngr_val_D;
      dmemreq_type_X  <= dmemreq_type_D;
      is_lw_X         <= is_lw_D;
      wb_result_sel_X <= wb_result_sel_D;
      stats_en_wen_X  <= stats_en_wen_D;
      br_type_X       <= br_type_D;
      jmp_type_X      <= jmp_type_D;
      ex_result_sel_X <= ex_result_sel_D;
      btb_hit_X       <= btb_hit_D;
      is_mul_X        <= is_mul_D;
    end

  // branch logic, redirect PC in F if branch is taken
  logic branch_X;
  assign branch_X = val_X && (br_type_X != br_na) &&
            (  (br_type_X == br_bne && !br_cond_eq_X) //bne
            || (br_type_X == br_beq && br_cond_eq_X) //beq
            || (br_type_X == br_blt && br_cond_lt_X) //blt
            || (br_type_X == br_bge && (!br_cond_lt_X || br_cond_eq_X))
            || (br_type_X == br_bltu && br_cond_ltu_X) //blt
            || (br_type_X == br_bgeu && (!br_cond_ltu_X || br_cond_eq_X))
            ); //beq


  logic jalr_X;
  assign jalr_X = val_X && (jmp_type_X == jmp_X);
  logic branch_or_jump_X;
  assign branch_or_jump_X = val_X && (jalr_X || branch_X);

  always_comb begin
    if (val_X) begin
      if (jmp_type_X == jmp_D) begin
        // If there was a branch in D, it's already been handled, so don't do anything.
        // But, if there was a branch in D, then it was a JAL, so we can always write
        // taken.
        pc_redirect_X = PC_BRANCHED_CORRECTLY;
        btb_write_config_X = PROC_BTB_WRITE_TAKEN;
      end else begin
        if (btb_hit_X) begin
          if (branch_or_jump_X) begin
            if (btb_correct_X) begin
              pc_redirect_X = PC_BRANCHED_CORRECTLY;
              btb_write_config_X = PROC_BTB_WRITE_TAKEN;
            end else begin
              pc_redirect_X = PC_BRANCHED_TO_WRONG_INST;
              btb_write_config_X = PROC_BTB_WRITE_TAKEN;
            end
          end else begin
            pc_redirect_X = PC_SHOULD_NOT_HAVE_BRANCHED;
            btb_write_config_X = PROC_BTB_WRITE_NOT_TAKEN;
          end
        end else begin
          if (branch_or_jump_X) begin
            pc_redirect_X = PC_BRANCHED_TO_WRONG_INST;
            btb_write_config_X = PROC_BTB_WRITE_TAKEN;
          end else begin
            pc_redirect_X = PC_BRANCHED_CORRECTLY;
            btb_write_config_X = PROC_BTB_WRITE_NONE;
          end
        end
      end
    end else begin
      pc_redirect_X = PC_BRANCHED_CORRECTLY;
      btb_write_config_X = PROC_BTB_WRITE_NONE;
    end
  end

  // If jump register, then the target jump address is from the ALU
  // Otherwise, it's from the decode stage
  assign br_jmp_sel_X = jalr_X ? 1'b1 : 1'b0; //branch_X ? 1'b0 : (jalr_X ? 1'b1 : 1'bx);
  // In target the BTB writes is controlled by a similiar signal to the one above
  // The only difference is we want to use 1'b0, the branch target, even if it
  // is not a branch in X, because if it was a JAL, then the logic above will
  // still trigger a write.
  // assign btb_write_target_sel_X = jalr_X ? 1'b1 : 1'b0;


  // ostall due to dmemreq not ready.
  logic ostall_dmemreq_X;
  assign ostall_dmemreq_X = val_X && ( dmemreq_type_X != nr ) && !dmemreq_rdy;

  logic ostall_mul_X;
  assign ostall_mul_X = val_X && (is_mul_X && !imul_resp_val_X);

  assign ostall_X = val_X && (ostall_dmemreq_X || ostall_mul_X);

  // osquash due to taken branch, notice we can't osquash if current
  // stage stalls, otherwise we will send osquash twice.

  assign osquash_X = val_X && !stall_X && (pc_redirect_X != PC_BRANCHED_CORRECTLY);

  // stall and squash used in X stage

  assign stall_X = val_X && ( ostall_X || ostall_M || ostall_W );

  // set dmemreq_val only if not stalling

  assign dmemreq_val = val_X && !stall_X && ( dmemreq_type_X != nr );

  // Multiplier ready logic
  assign imul_resp_rdy_X = val_X && !stall_X && is_mul_X;

  // Valid signal for the next stage

  logic  next_val_X;
  assign next_val_X = val_X && !stall_X;

  //----------------------------------------------------------------------
  // M stage
  //----------------------------------------------------------------------

  // Register enable logic

  assign reg_en_M  = !stall_M;

  logic [31:0] inst_M;
  logic [1:0]  dmemreq_type_M;
  logic        rf_wen_pending_M;
  logic [4:0]  rf_waddr_M;
  logic        proc2mngr_val_M;
  logic        stats_en_wen_M;

  // Pipeline register

  always_ff @( posedge clk )
    if (reset) begin
      val_M            <= 1'b0;
      stats_en_wen_X   <= 1'b0;
    end else if (reg_en_M) begin
      val_M            <= next_val_X;
      rf_wen_pending_M <= rf_wen_pending_X;
      inst_M           <= inst_X;
      rf_waddr_M       <= rf_waddr_X;
      proc2mngr_val_M  <= proc2mngr_val_X;
      dmemreq_type_M   <= dmemreq_type_X;
      wb_result_sel_M  <= wb_result_sel_X;
      stats_en_wen_M   <= stats_en_wen_X;
    end

  // ostall due to dmemresp not valid

  assign ostall_M = val_M && ( dmemreq_type_M != nr ) && !dmemresp_val;

  // stall M

  assign stall_M = val_M && ( ostall_M || ostall_W );

  // Set dmemresp_rdy if valid and not stalling and this is a lw/sw

  assign dmemresp_rdy = val_M && !stall_M && ( dmemreq_type_M != nr );

  // Valid signal for the next stage

  logic  next_val_M;
  assign next_val_M = val_M && !stall_M;

  //----------------------------------------------------------------------
  // W stage
  //----------------------------------------------------------------------

  // Register enable logic

  assign reg_en_W = !stall_W;

  logic [31:0] inst_W;
  logic        proc2mngr_val_W;
  logic        rf_wen_pending_W;
  logic        stats_en_wen_pending_W;

  // Pipeline registers

  always_ff @( posedge clk ) begin
    if (reset) begin
      val_W            <= 1'b0;
      stats_en_wen_pending_W   <= 1'b0;
    end else if (reg_en_W) begin
      val_W            <= next_val_M;
      rf_wen_pending_W <= rf_wen_pending_M;
      inst_W           <= inst_M;
      rf_waddr_W       <= rf_waddr_M;
      proc2mngr_val_W  <= proc2mngr_val_M;
      stats_en_wen_pending_W   <= stats_en_wen_M;
    // Generic Parameters -- yes or no
    // Magic numbers were here!
    end
  end

  // write enable

  assign rf_wen_W       = val_W && rf_wen_pending_W;
  assign stats_en_wen_W = val_W && stats_en_wen_pending_W;

  // ostall due to proc2mngr

  assign ostall_W = val_W && proc2mngr_val_W && !proc2mngr_rdy;

  // stall and squash signal used in W stage

  assign stall_W = val_W && ostall_W;

  // proc2mngr port

  assign proc2mngr_val = val_W && !stall_W && proc2mngr_val_W;

  assign commit_inst = val_W && !stall_W;

endmodule

`endif
