//=========================================================================
// 5-Stage Simple Pipelined Processor
//=========================================================================

`ifndef LAB2_PROC_PIPELINED_PROC_BASE_V
`define LAB2_PROC_PIPELINED_PROC_BASE_V

`include "vc/mem-msgs.v"
`include "vc/queues.v"
`include "vc/trace.v"

`include "lab2_proc/TinyRV2InstVRTL.v"
`include "lab2_proc/DropUnitVRTL.v"
`include "lab2_proc/ProcVRTL.v"

module lab2_proc_ProcBaseVRTL
#(
  parameter p_num_cores = 1
)
(
  input  logic         clk,
  input  logic         reset,

  // core_id is an input port rather than a parameter so that
  // the module only needs to be compiled once. If it were a parameter,
  // each core would be compiled separately.
  input  logic [31:0]  core_id,

  // From mngr streaming port

  input  logic [31:0]  mngr2proc_msg,
  input  logic         mngr2proc_val,
  output logic         mngr2proc_rdy,

  // To mngr streaming port

  output logic [31:0]  proc2mngr_msg,
  output logic         proc2mngr_val,
  input  logic         proc2mngr_rdy,

  // Instruction Memory Request Port

  output mem_req_4B_t  imemreq_msg,
  output logic         imemreq_val,
  input  logic         imemreq_rdy,

  // Instruction Memory Response Port

  input  mem_resp_4B_t imemresp_msg,
  input  logic         imemresp_val,
  output logic         imemresp_rdy,

  // Data Memory Request Port

  output mem_req_4B_t  dmemreq_msg,
  output logic         dmemreq_val,
  input  logic         dmemreq_rdy,

  // Data Memory Response Port

  input  mem_resp_4B_t dmemresp_msg,
  input  logic         dmemresp_val,
  output logic         dmemresp_rdy,

  // stats output

  output logic         commit_inst,

  output logic         stats_en

);

lab2_proc_ProcVRTL#(
    .p_num_cores(p_num_cores),
    .p_type(`PROC_DESIGN_STALLING),
    .p_btb(`PROC_DESIGN_NO_BTB)
) proc (.*);


`ifndef SYNTHESIS

`VC_TRACE_BEGIN
proc.line_trace(trace_str);
`VC_TRACE_END

`endif

endmodule

`endif
