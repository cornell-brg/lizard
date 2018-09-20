//========================================================================
// Verilog Components: Test Memory with Random Delays
//========================================================================
// This is dual-ported test memory that handles a limited subset of
// memory request messages and returns memory response messages.

`ifndef VC_TEST_RAND_DELAY_MEM_2PORTS_V
`define VC_TEST_RAND_DELAY_MEM_2PORTS_V

`include "vc/mem-msgs.v"
`include "vc/TestMem_2ports.v"
`include "vc/TestRandDelay.v"
`include "vc/trace.v"

module vc_TestRandDelayMem_2ports
#(
  parameter p_mem_nbytes   = 1024, // size of physical memory in bytes
  parameter p_opaque_nbits = 8,    // mem message opaque field num bits
  parameter p_addr_nbits   = 32,   // mem message address num bits
  parameter p_data_nbits   = 32,   // mem message data num bits
  parameter p_reset_to_x   = 1,    // reset all values to X's

  // Shorter names for message type, not to be set from outside the module
  parameter o = p_opaque_nbits,
  parameter a = p_addr_nbits,
  parameter d = p_data_nbits,

  // Local constants not meant to be set from outside the module
  parameter c_req_nbits  = `VC_MEM_REQ_MSG_NBITS(o,a,d),
  parameter c_resp_nbits = `VC_MEM_RESP_MSG_NBITS(o,d)
)(
  input  logic                    clk,
  input  logic                    reset,

  // clears the content of memory

  input  logic                    mem_clear,

  // maximum delay

  input  logic [31:0]             max_delay,

  // Memory request interface port 0

  input  logic                    memreq0_val,
  output logic                    memreq0_rdy,
  input  logic [c_req_nbits-1:0]  memreq0_msg,

  // Memory request interface port 1

  input  logic                    memreq1_val,
  output logic                    memreq1_rdy,
  input  logic [c_req_nbits-1:0]  memreq1_msg,

  // Memory response interface port 0

  output logic                    memresp0_val,
  input  logic                    memresp0_rdy,
  output logic [c_resp_nbits-1:0] memresp0_msg,

  // Memory response interface port 1

  output logic                    memresp1_val,
  input  logic                    memresp1_rdy,
  output logic [c_resp_nbits-1:0] memresp1_msg
);

  //------------------------------------------------------------------------
  // Dual ported test memory
  //------------------------------------------------------------------------

  logic                    mem_memreq0_val;
  logic                    mem_memreq0_rdy;
  logic [c_req_nbits-1:0]  mem_memreq0_msg;

  logic                    mem_memreq1_val;
  logic                    mem_memreq1_rdy;
  logic [c_req_nbits-1:0]  mem_memreq1_msg;


  logic                    mem_memresp0_val;
  logic                    mem_memresp0_rdy;
  logic [c_resp_nbits-1:0] mem_memresp0_msg;

  logic                    mem_memresp1_val;
  logic                    mem_memresp1_rdy;
  logic [c_resp_nbits-1:0] mem_memresp1_msg;

  //------------------------------------------------------------------------
  // Test random delay
  //------------------------------------------------------------------------

  vc_TestRandDelay#(c_req_nbits) rand_req_delay0
  (
    .clk       (clk),
    .reset     (reset),

    // dividing the max delay by two because we have delay for both in and
    // out
    .max_delay (max_delay >> 1),

    .in_val    (memreq0_val),
    .in_rdy    (memreq0_rdy),
    .in_msg    (memreq0_msg),

    .out_val   (mem_memreq0_val),
    .out_rdy   (mem_memreq0_rdy),
    .out_msg   (mem_memreq0_msg)

  );

  vc_TestRandDelay#(c_req_nbits) rand_req_delay1
  (
    .clk       (clk),
    .reset     (reset),

    // dividing the max delay by two because we have delay for both in and
    // out
    .max_delay (max_delay >> 1),

    .in_val    (memreq1_val),
    .in_rdy    (memreq1_rdy),
    .in_msg    (memreq1_msg),

    .out_val   (mem_memreq1_val),
    .out_rdy   (mem_memreq1_rdy),
    .out_msg   (mem_memreq1_msg)

   );

  vc_TestMem_2ports
  #(
    .p_mem_nbytes   (p_mem_nbytes),
    .p_opaque_nbits (p_opaque_nbits),
    .p_addr_nbits   (p_addr_nbits),
    .p_data_nbits   (p_data_nbits)
  )
  mem
  (
    .clk          (clk),
    .reset        (reset),
    .mem_clear    (mem_clear),

    .memreq0_val  (mem_memreq0_val),
    .memreq0_rdy  (mem_memreq0_rdy),
    .memreq0_msg  (mem_memreq0_msg),

    .memreq1_val  (mem_memreq1_val),
    .memreq1_rdy  (mem_memreq1_rdy),
    .memreq1_msg  (mem_memreq1_msg),

    .memresp0_val (mem_memresp0_val),
    .memresp0_rdy (mem_memresp0_rdy),
    .memresp0_msg (mem_memresp0_msg),

    .memresp1_val (mem_memresp1_val),
    .memresp1_rdy (mem_memresp1_rdy),
    .memresp1_msg (mem_memresp1_msg)
  );

  //------------------------------------------------------------------------
  // Test random delay
  //------------------------------------------------------------------------

  vc_TestRandDelay#(c_resp_nbits) rand_resp_delay0
  (
    .clk       (clk),
    .reset     (reset),

    // dividing the max delay by two because we have delay for both in and
    // out
    .max_delay (max_delay >> 1),

    .in_val    (mem_memresp0_val),
    .in_rdy    (mem_memresp0_rdy),
    .in_msg    (mem_memresp0_msg),

    .out_val   (memresp0_val),
    .out_rdy   (memresp0_rdy),
    .out_msg   (memresp0_msg)
  );

  vc_TestRandDelay#(c_resp_nbits) rand_resp_delay1
  (
    .clk       (clk),
    .reset     (reset),

    // dividing the max delay by two because we have delay for both in and
    // out
    .max_delay (max_delay >> 1),

    .in_val    (mem_memresp1_val),
    .in_rdy    (mem_memresp1_rdy),
    .in_msg    (mem_memresp1_msg),

    .out_val   (memresp1_val),
    .out_rdy   (memresp1_rdy),
    .out_msg   (memresp1_msg)
  );

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------

  vc_MemReqMsgTrace#(o,a,d) memreq0_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (memreq0_val),
    .rdy   (memreq0_rdy),
    .msg   (memreq0_msg)
  );

  vc_MemReqMsgTrace#(o,a,d) memreq1_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (memreq1_val),
    .rdy   (memreq1_rdy),
    .msg   (memreq1_msg)
  );

  vc_MemRespMsgTrace#(o,d) memresp0_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (memresp0_val),
    .rdy   (memresp0_rdy),
    .msg   (memresp0_msg)
  );

  vc_MemRespMsgTrace#(o,d) memresp1_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (memresp1_val),
    .rdy   (memresp1_rdy),
    .msg   (memresp1_msg)
  );

  `VC_TRACE_BEGIN
  begin

    memreq0_trace.line_trace( trace_str );
    vc_trace.append_str( trace_str, "|" );
    memreq1_trace.line_trace( trace_str );

    vc_trace.append_str( trace_str, "()" );

    memresp0_trace.line_trace( trace_str );
    vc_trace.append_str( trace_str, "|" );
    memresp1_trace.line_trace( trace_str );

  end
  `VC_TRACE_END

endmodule

`endif /* VC_TEST_RAND_DELAY_MEM_2PORTS_V */

