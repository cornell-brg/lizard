//========================================================================
// 1-Core Processor-Cache-Network
//========================================================================

`ifndef LAB5_MCORE_SINGLE_CORE_V
`define LAB5_MCORE_SINGLE_CORE_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"

`include "lab2_proc/ProcAltVRTL.v"
`include "lab3_mem/BlockingCacheAltVRTL.v"

module lab5_mcore_SingleCoreVRTL
#(
  parameter dummy = 0 // need this to keep pymtl from automatically adding parameters
)
(
  input  logic                       clk,
  input  logic                       reset,

  // proc manager ports

  input  logic [31:0]                mngr2proc_msg,
  input  logic                       mngr2proc_val,
  output logic                       mngr2proc_rdy,

  output logic [31:0]                proc2mngr_msg,
  output logic                       proc2mngr_val,
  input  logic                       proc2mngr_rdy,

  output mem_req_16B_t               imemreq_msg,
  output logic                       imemreq_val,
  input  logic                       imemreq_rdy,

  input  mem_resp_16B_t              imemresp_msg,
  input  logic                       imemresp_val,
  output logic                       imemresp_rdy,

  output mem_req_16B_t               dmemreq_msg,
  output logic                       dmemreq_val,
  input  logic                       dmemreq_rdy,

  input  mem_resp_16B_t              dmemresp_msg,
  input  logic                       dmemresp_val,
  output logic                       dmemresp_rdy,

  output logic                       stats_en,
  output logic                       commit_inst,
  output logic                       icache_miss,
  output logic                       icache_access,
  output logic                       dcache_miss,
  output logic                       dcache_access
);

  mem_req_4B_t                  icache_req_msg;
  logic                         icache_req_val;
  logic                         icache_req_rdy;

  mem_resp_4B_t                 icache_resp_msg;
  logic                         icache_resp_val;
  logic                         icache_resp_rdy;

  mem_req_4B_t                  dcache_req_msg;
  logic                         dcache_req_val;
  logic                         dcache_req_rdy;

  mem_resp_4B_t                 dcache_resp_msg;
  logic                         dcache_resp_val;
  logic                         dcache_resp_rdy;

  logic                         proc_commit_inst;

  // processor

  lab2_proc_ProcAltVRTL proc
  (
    .clk           (clk),
    .reset         (reset),

    .core_id       (32'd0),

    .imemreq_msg   (icache_req_msg),
    .imemreq_val   (icache_req_val),
    .imemreq_rdy   (icache_req_rdy),

    .imemresp_msg  (icache_resp_msg),
    .imemresp_val  (icache_resp_val),
    .imemresp_rdy  (icache_resp_rdy),

    .dmemreq_msg   (dcache_req_msg),
    .dmemreq_val   (dcache_req_val),
    .dmemreq_rdy   (dcache_req_rdy),

    .dmemresp_msg  (dcache_resp_msg),
    .dmemresp_val  (dcache_resp_val),
    .dmemresp_rdy  (dcache_resp_rdy),

    .mngr2proc_msg (mngr2proc_msg),
    .mngr2proc_val (mngr2proc_val),
    .mngr2proc_rdy (mngr2proc_rdy),

    .proc2mngr_msg (proc2mngr_msg),
    .proc2mngr_val (proc2mngr_val),
    .proc2mngr_rdy (proc2mngr_rdy),

    .stats_en      (stats_en),
    .commit_inst   (proc_commit_inst)
  );

  // instruction cache

  lab3_mem_BlockingCacheAltVRTL
  #(
    .p_num_banks   (1)
  )
  icache
  (
    .clk           (clk),
    .reset         (reset),

    .cachereq_msg  (icache_req_msg),
    .cachereq_val  (icache_req_val),
    .cachereq_rdy  (icache_req_rdy),

    .cacheresp_msg (icache_resp_msg),
    .cacheresp_val (icache_resp_val),
    .cacheresp_rdy (icache_resp_rdy),

    .memreq_msg    (imemreq_msg),
    .memreq_val    (imemreq_val),
    .memreq_rdy    (imemreq_rdy),

    .memresp_msg   (imemresp_msg),
    .memresp_val   (imemresp_val),
    .memresp_rdy   (imemresp_rdy)

  );

  // data cache

  lab3_mem_BlockingCacheAltVRTL
  #(
    .p_num_banks   (1)
  )
  dcache
  (
    .clk           (clk),
    .reset         (reset),

    .cachereq_msg  (dcache_req_msg),
    .cachereq_val  (dcache_req_val),
    .cachereq_rdy  (dcache_req_rdy),

    .cacheresp_msg (dcache_resp_msg),
    .cacheresp_val (dcache_resp_val),
    .cacheresp_rdy (dcache_resp_rdy),

    .memreq_msg    (dmemreq_msg),
    .memreq_val    (dmemreq_val),
    .memreq_rdy    (dmemreq_rdy),

    .memresp_msg   (dmemresp_msg),
    .memresp_val   (dmemresp_val),
    .memresp_rdy   (dmemresp_rdy)

  );

  // This piece of code is used to help simulator calculate the cache
  // miss/access, miss rate, and committed instruction count

  assign commit_inst   = proc_commit_inst;
  assign icache_miss   = icache_resp_val & icache_resp_rdy & ~icache_resp_msg.test[0];
  assign icache_access = icache_req_val  & icache_req_rdy;
  assign dcache_miss   = dcache_resp_val & dcache_resp_rdy & ~dcache_resp_msg.test[0];
  assign dcache_access = dcache_req_val  & dcache_req_rdy;

  `VC_TRACE_BEGIN
  begin
    proc.line_trace( trace_str );
    vc_trace.append_str( trace_str, "|" );
    icache.line_trace( trace_str );
    dcache.line_trace( trace_str );
  end
  `VC_TRACE_END

endmodule

`endif /* LAB5_MCORE_SINGLE_CORE_V */
