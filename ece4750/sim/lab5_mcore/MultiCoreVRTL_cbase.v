//========================================================================
// 1-Core Processor-Cache-Network
//========================================================================

`ifndef LAB5_MCORE_MULTI_CORE_V
`define LAB5_MCORE_MULTI_CORE_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"
`include "lab5_mcore/McoreDataCacheVRTL.v"
`include "lab2_proc/ProcAltVRTL.v"
`include "lab3_mem/BlockingCacheBaseVRTL.v"


//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include components
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab5_mcore_MultiCoreVRTL
(
  input  logic                       clk,
  input  logic                       reset,

  input  logic [c_num_cores-1:0][31:0] mngr2proc_msg,
  input  logic [c_num_cores-1:0]       mngr2proc_val,
  output logic [c_num_cores-1:0]       mngr2proc_rdy,

  output logic [c_num_cores-1:0][31:0] proc2mngr_msg,
  output logic [c_num_cores-1:0]       proc2mngr_val,
  input  logic [c_num_cores-1:0]       proc2mngr_rdy,

  output mem_req_16B_t                 imemreq_msg,
  output logic                         imemreq_val,
  input  logic                         imemreq_rdy,

  input  mem_resp_16B_t                imemresp_msg,
  input  logic                         imemresp_val,
  output logic                         imemresp_rdy,

  output mem_req_16B_t                 dmemreq_msg,
  output logic                         dmemreq_val,
  input  logic                         dmemreq_rdy,

  input  mem_resp_16B_t                dmemresp_msg,
  input  logic                         dmemresp_val,
  output logic                         dmemresp_rdy,

  //  Only takes Core 0's stats_en to the interface
  output logic                         stats_en,
  output logic [c_num_cores-1:0]       commit_inst,
  output logic [c_num_cores-1:0]       icache_miss,
  output logic [c_num_cores-1:0]       icache_access,
  output logic [c_num_cores-1:0]       dcache_miss,
  output logic [c_num_cores-1:0]       dcache_access
);

  localparam c_num_cores = 4;

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Instantiate modules and wires
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  mem_req_4B_t  [c_num_cores-1:0]      icache_req_msg;
  logic         [c_num_cores-1:0]      icache_req_val;
  logic         [c_num_cores-1:0]      icache_req_rdy;

  mem_resp_4B_t [c_num_cores-1:0]      icache_resp_msg;
  logic         [c_num_cores-1:0]      icache_resp_val;
  logic         [c_num_cores-1:0]      icache_resp_rdy;

  mem_req_4B_t  [c_num_cores-1:0]      dcache_req_msg;
  logic         [c_num_cores-1:0]      dcache_req_val;
  logic         [c_num_cores-1:0]      dcache_req_rdy;

  mem_resp_4B_t [c_num_cores-1:0]      dcache_resp_msg;
  logic         [c_num_cores-1:0]      dcache_resp_val;
  logic         [c_num_cores-1:0]      dcache_resp_rdy;

  lab5_mcore_McoreDataCacheVRTL dcache
  (
    .clk                (clk),
    .reset              (reset),

    .procreq_msg        (dcache_req_msg),
    .procreq_val        (dcache_req_val),
    .procreq_rdy        (dcache_req_rdy),

    .procresp_msg       (dcache_resp_msg),
    .procresp_val       (dcache_resp_val),
    .procresp_rdy       (dcache_resp_rdy),

    .mainmemreq_msg     (dmemreq_msg),
    .mainmemreq_val     (dmemreq_val),
    .mainmemreq_rdy     (dmemreq_rdy),

    .mainmemresp_msg    (dmemresp_msg),
    .mainmemresp_val    (dmemresp_val),
    .mainmemresp_rdy    (dmemresp_rdy),

    .dcache_miss        (dcache_miss),
    .dcache_access      (dcache_access)
  );

  // icache refill net
  mem_req_16B_t  [c_num_cores-1:0] icache_net_memreq_msg;
  logic          [c_num_cores-1:0] icache_net_memreq_val;
  logic          [c_num_cores-1:0] icache_net_memreq_rdy;

  mem_resp_16B_t [c_num_cores-1:0] icache_net_memresp_msg;
  logic          [c_num_cores-1:0] icache_net_memresp_val;
  logic          [c_num_cores-1:0] icache_net_memresp_rdy;

  mem_req_16B_t  [c_num_cores-1:0] imemreq_refill_msg;
  logic          [c_num_cores-1:0] imemreq_refill_val;
  logic          [c_num_cores-1:0] imemreq_refill_rdy;

  mem_resp_16B_t [c_num_cores-1:0] imemresp_refill_msg;
  logic          [c_num_cores-1:0] imemresp_refill_val;
  logic          [c_num_cores-1:0] imemresp_refill_rdy;

  lab5_mcore_MemNetVRTL icache_refill_net
  (
    .clk           (clk),
    .reset         (reset),

    .memreq_msg  (icache_net_memreq_msg),
    .memreq_val  (icache_net_memreq_val),
    .memreq_rdy  (icache_net_memreq_rdy),

    .memresp_msg (icache_net_memresp_msg),
    .memresp_val (icache_net_memresp_val),
    .memresp_rdy (icache_net_memresp_rdy),

    .mainmemreq_msg  (imemreq_refill_msg),
    .mainmemreq_val  (imemreq_refill_val),
    .mainmemreq_rdy  (imemreq_refill_rdy),

    .mainmemresp_msg (imemresp_refill_msg),
    .mainmemresp_val (imemresp_refill_val),
    .mainmemresp_rdy (imemresp_refill_rdy)
  );

  assign imemreq_msg = imemreq_refill_msg[0];
  assign imemreq_val = imemreq_refill_val[0];
  assign imemreq_refill_rdy = { {c_num_cores-1{1'b0}}, imemreq_rdy };

  assign imemresp_refill_msg[0] = imemresp_msg;
  assign imemresp_refill_val = { {c_num_cores-1{1'b0}}, imemresp_val };
  assign imemresp_rdy = imemresp_refill_rdy[0];

  logic [c_num_cores-1:0]       cores_stats_en;
  assign stats_en = cores_stats_en[0];

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Instantiate caches and connect them to cores
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  genvar i;
  generate
  for ( i = 0; i < c_num_cores; i = i + 1 ) begin: CORES_CACHES
    lab2_proc_ProcAltVRTL
    #(
      .p_num_cores             (c_num_cores)
    )
    proc
    (
      .clk           (clk),
      .reset         (reset),

      .core_id       (i),

      .imemreq_msg   (icache_req_msg[i]),
      .imemreq_val   (icache_req_val[i]),
      .imemreq_rdy   (icache_req_rdy[i]),

      .imemresp_msg  (icache_resp_msg[i]),
      .imemresp_val  (icache_resp_val[i]),
      .imemresp_rdy  (icache_resp_rdy[i]),

      .dmemreq_msg   (dcache_req_msg[i]),
      .dmemreq_val   (dcache_req_val[i]),
      .dmemreq_rdy   (dcache_req_rdy[i]),

      .dmemresp_msg  (dcache_resp_msg[i]),
      .dmemresp_val  (dcache_resp_val[i]),
      .dmemresp_rdy  (dcache_resp_rdy[i]),

      .mngr2proc_msg (mngr2proc_msg[i]),
      .mngr2proc_val (mngr2proc_val[i]),
      .mngr2proc_rdy (mngr2proc_rdy[i]),

      .proc2mngr_msg (proc2mngr_msg[i]),
      .proc2mngr_val (proc2mngr_val[i]),
      .proc2mngr_rdy (proc2mngr_rdy[i]),

      .stats_en      (cores_stats_en[i]),
      .commit_inst   (commit_inst[i])
    );

    // instruction cache

    lab3_mem_BlockingCacheBaseVRTL
    #(
      .p_num_banks   (1)
    )
    icache
    (
      .clk           (clk),
      .reset         (reset),

      .cachereq_msg  (icache_req_msg[i]),
      .cachereq_val  (icache_req_val[i]),
      .cachereq_rdy  (icache_req_rdy[i]),

      .cacheresp_msg (icache_resp_msg[i]),
      .cacheresp_val (icache_resp_val[i]),
      .cacheresp_rdy (icache_resp_rdy[i]),

      .memreq_msg    (icache_net_memreq_msg[i]),
      .memreq_val    (icache_net_memreq_val[i]),
      .memreq_rdy    (icache_net_memreq_rdy[i]),

      .memresp_msg   (icache_net_memresp_msg[i]),
      .memresp_val   (icache_net_memresp_val[i]),
      .memresp_rdy   (icache_net_memresp_rdy[i])

    );

    assign icache_miss[i] = icache_resp_rdy[i] & icache_resp_val[i] & (! icache_resp_msg[i].test[0] );
    assign icache_access[i] = icache_req_rdy[i] & icache_req_val[i];
  end
  endgenerate

  // Only takes proc0's stats_en
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: hook up stats and add icache stats
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  `VC_TRACE_BEGIN
  begin

    // This is staffs' line trace, which assume the processors and icaches
    // are instantiated in using generate statement, and the data cache
    // system is instantiated with the name dcache. You can add net to the
    // line trace.
    // Feel free to revamp it or redo it based on your need.

    CORES_CACHES[0].icache.line_trace( trace_str );
    CORES_CACHES[0].proc.line_trace( trace_str );
    CORES_CACHES[1].icache.line_trace( trace_str );
    CORES_CACHES[1].proc.line_trace( trace_str );
    CORES_CACHES[2].icache.line_trace( trace_str );
    CORES_CACHES[2].proc.line_trace( trace_str );
    CORES_CACHES[3].icache.line_trace( trace_str );
    CORES_CACHES[3].proc.line_trace( trace_str );

    dcache.line_trace( trace_str );
  end
  `VC_TRACE_END

endmodule

`endif /* LAB5_MCORE_MULTI_CORE_V */
