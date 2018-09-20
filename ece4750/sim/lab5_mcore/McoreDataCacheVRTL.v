//========================================================================
// 1-Core Processor-Cache-Network
//========================================================================

`ifndef LAB5_MCORE_MCORE_DATA_CACHE_V
`define LAB5_MCORE_MCORE_DATA_CACHE_V

`include "vc/mem-msgs.v"
`include "vc/trace.v"

`include "lab3_mem/BlockingCacheAltVRTL.v"
`include "lab5_mcore/CacheNetVRTL.v"
`include "lab5_mcore/MemNetVRTL.v"

module lab5_mcore_McoreDataCacheVRTL
(
  input  logic                       clk,
  input  logic                       reset,

  input  mem_req_4B_t  [c_num_cores-1:0] procreq_msg,
  input  logic         [c_num_cores-1:0] procreq_val,
  output logic         [c_num_cores-1:0] procreq_rdy,

  output mem_resp_4B_t [c_num_cores-1:0] procresp_msg,
  output logic         [c_num_cores-1:0] procresp_val,
  input  logic         [c_num_cores-1:0] procresp_rdy,

  output mem_req_16B_t                   mainmemreq_msg,
  output logic                           mainmemreq_val,
  input  logic                           mainmemreq_rdy,

  input  mem_resp_16B_t                  mainmemresp_msg,
  input  logic                           mainmemresp_val,
  output logic                           mainmemresp_rdy,

  // Ports used for statistics gathering
  output logic         [c_num_cores-1:0] dcache_miss,
  output logic         [c_num_cores-1:0] dcache_access
);

  localparam c_num_cores = 4;

  // declare network wires

  mem_req_4B_t   [c_num_cores-1:0] cachereq_msg;
  logic          [c_num_cores-1:0] cachereq_val;
  logic          [c_num_cores-1:0] cachereq_rdy;

  mem_resp_4B_t  [c_num_cores-1:0] cacheresp_msg;
  logic          [c_num_cores-1:0] cacheresp_val;
  logic          [c_num_cores-1:0] cacheresp_rdy;

  mem_req_16B_t  [c_num_cores-1:0] memreq_msg;
  logic          [c_num_cores-1:0] memreq_val;
  logic          [c_num_cores-1:0] memreq_rdy;

  mem_resp_16B_t [c_num_cores-1:0] memresp_msg;
  logic          [c_num_cores-1:0] memresp_val;
  logic          [c_num_cores-1:0] memresp_rdy;

  genvar i;
  generate
  for ( i = 0; i < c_num_cores; i = i + 1 ) begin: DCACHES

    // data cache

    lab3_mem_BlockingCacheAltVRTL
    #(
      .p_num_banks          (c_num_cores)
    )
    dcache
    (
      .clk           (clk),
      .reset         (reset),

      .cachereq_msg  (cachereq_msg[i]),
      .cachereq_val  (cachereq_val[i]),
      .cachereq_rdy  (cachereq_rdy[i]),

      .cacheresp_msg (cacheresp_msg[i]),
      .cacheresp_val (cacheresp_val[i]),
      .cacheresp_rdy (cacheresp_rdy[i]),

      .memreq_msg    (memreq_msg[i]),
      .memreq_val    (memreq_val[i]),
      .memreq_rdy    (memreq_rdy[i]),

      .memresp_msg   (memresp_msg[i]),
      .memresp_val   (memresp_val[i]),
      .memresp_rdy   (memresp_rdy[i])

    );

    // Collect statistics for this cache
    assign dcache_miss[i] = cacheresp_rdy[i] & cacheresp_val[i] & (! cacheresp_msg[i].test[0] );
    assign dcache_access[i] = cachereq_rdy[i] & cachereq_val[i];
  end
  endgenerate

  // dcache request net

  lab5_mcore_CacheNetVRTL proc_dcache_net
  (
    .clk           (clk),
    .reset         (reset),

    .procreq_msg   (procreq_msg),
    .procreq_val   (procreq_val),
    .procreq_rdy   (procreq_rdy),

    .procresp_msg  (procresp_msg),
    .procresp_val  (procresp_val),
    .procresp_rdy  (procresp_rdy),

    .cachereq_msg  (cachereq_msg),
    .cachereq_val  (cachereq_val),
    .cachereq_rdy  (cachereq_rdy),

    .cacheresp_msg (cacheresp_msg),
    .cacheresp_val (cacheresp_val),
    .cacheresp_rdy (cacheresp_rdy)
  );

  // dcache refill net
  // Since there's only a single memory port,
  // need to clear val/rdy for the other ports

  mem_req_16B_t  [c_num_cores-1:0] mainmemreq_refill_msg;
  logic          [c_num_cores-1:0] mainmemreq_refill_val;
  logic          [c_num_cores-1:0] mainmemreq_refill_rdy;

  mem_resp_16B_t [c_num_cores-1:0] mainmemresp_refill_msg;
  logic          [c_num_cores-1:0] mainmemresp_refill_val;
  logic          [c_num_cores-1:0] mainmemresp_refill_rdy;

  lab5_mcore_MemNetVRTL dcache_refill_net
  (
    .clk           (clk),
    .reset         (reset),

    .memreq_msg  (memreq_msg),
    .memreq_val  (memreq_val),
    .memreq_rdy  (memreq_rdy),

    .memresp_msg (memresp_msg),
    .memresp_val (memresp_val),
    .memresp_rdy (memresp_rdy),

    .mainmemreq_msg  (mainmemreq_refill_msg),
    .mainmemreq_val  (mainmemreq_refill_val),
    .mainmemreq_rdy  (mainmemreq_refill_rdy),

    .mainmemresp_msg (mainmemresp_refill_msg),
    .mainmemresp_val (mainmemresp_refill_val),
    .mainmemresp_rdy (mainmemresp_refill_rdy)
  );

  assign mainmemreq_msg = mainmemreq_refill_msg[0];
  assign mainmemreq_val = mainmemreq_refill_val[0];
  assign mainmemreq_refill_rdy = { {c_num_cores-1{1'b0}}, mainmemreq_rdy };

  assign mainmemresp_refill_msg[0] = mainmemresp_msg;
  assign mainmemresp_refill_val = { {c_num_cores-1{1'b0}}, mainmemresp_val };
  assign mainmemresp_rdy = mainmemresp_refill_rdy[0];

  `VC_TRACE_BEGIN
  begin
    DCACHES[0].dcache.line_trace( trace_str );
    DCACHES[1].dcache.line_trace( trace_str );
    DCACHES[2].dcache.line_trace( trace_str );
    DCACHES[3].dcache.line_trace( trace_str );
  end
  `VC_TRACE_END

endmodule

`endif /* LAB5_MCORE_MCORE_DATA_CACHE_V */
