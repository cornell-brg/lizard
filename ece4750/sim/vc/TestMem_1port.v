//========================================================================
// Verilog Components: Test Memory
//========================================================================
// This is single-ported test memory that handles a limited subset of
// memory request messages and returns memory response messages.

`ifndef VC_TEST_MEM_1PORT_V
`define VC_TEST_MEM_1PORT_V

`include "vc/mem-msgs.v"
`include "vc/queues.v"
`include "vc/assert.v"
`include "vc/trace.v"

//------------------------------------------------------------------------
// Test memory with two req/resp ports
//------------------------------------------------------------------------

module vc_TestMem_1port
#(
  parameter p_mem_nbytes   = 1024, // size of physical memory in bytes
  parameter p_opaque_nbits = 8,    // mem message opaque field num bits
  parameter p_addr_nbits   = 32,   // mem message address num bits
  parameter p_data_nbits   = 32,   // mem message data num bits

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

  // Memory request port interface

  input  logic                    memreq_val,
  output logic                    memreq_rdy,
  input  logic [c_req_nbits-1:0]  memreq_msg,

  // Memory response port interface

  output logic                    memresp_val,
  input  logic                    memresp_rdy,
  output logic [c_resp_nbits-1:0] memresp_msg
);

  //----------------------------------------------------------------------
  // Local parameters
  //----------------------------------------------------------------------

  // Size of a physical address for the memory in bits

  localparam c_physical_addr_nbits = $clog2(p_mem_nbytes);

  // Size of data entry in bytes

  localparam c_data_byte_nbits = (p_data_nbits/8);

  // Number of data entries in memory

  localparam c_num_blocks = p_mem_nbytes/c_data_byte_nbits;

  // Size of block address in bits

  localparam c_physical_block_addr_nbits = $clog2(c_num_blocks);

  // Size of block offset in bits

  localparam c_block_offset_nbits = $clog2(c_data_byte_nbits);

  // Shorthand for the message types

  localparam c_read       = `VC_MEM_REQ_MSG_TYPE_READ;
  localparam c_write      = `VC_MEM_REQ_MSG_TYPE_WRITE;
  localparam c_write_init = `VC_MEM_REQ_MSG_TYPE_WRITE_INIT;
  localparam c_amo_add    = `VC_MEM_REQ_MSG_TYPE_AMO_ADD;
  localparam c_amo_and    = `VC_MEM_REQ_MSG_TYPE_AMO_AND;
  localparam c_amo_or     = `VC_MEM_REQ_MSG_TYPE_AMO_OR;

  // Shorthand for the message field sizes

  localparam c_req_type_nbits    = `VC_MEM_REQ_MSG_TYPE_NBITS(o,a,d);
  localparam c_req_opaque_nbits  = `VC_MEM_REQ_MSG_OPAQUE_NBITS(o,a,d);
  localparam c_req_addr_nbits    = `VC_MEM_REQ_MSG_ADDR_NBITS(o,a,d);
  localparam c_req_len_nbits     = `VC_MEM_REQ_MSG_LEN_NBITS(o,a,d);
  localparam c_req_data_nbits    = `VC_MEM_REQ_MSG_DATA_NBITS(o,a,d);

  localparam c_resp_type_nbits   = `VC_MEM_RESP_MSG_TYPE_NBITS(o,d);
  localparam c_resp_opaque_nbits = `VC_MEM_RESP_MSG_OPAQUE_NBITS(o,d);
  localparam c_resp_len_nbits    = `VC_MEM_RESP_MSG_LEN_NBITS(o,d);
  localparam c_resp_data_nbits   = `VC_MEM_RESP_MSG_DATA_NBITS(o,d);

  //----------------------------------------------------------------------
  // Memory request buffers
  //----------------------------------------------------------------------
  // We use pipe queues here since in general we want our larger modules
  // to use registered inputs, but we want to reduce the overhead of
  // having two elements which would be required for full throughput with
  // normal queues. By using a pipe queues at the inputs and a bypass
  // queue at the output we cut and combinational paths through the test
  // memory (helping to avoid combinational loops) and also preserve our
  // registered input policy.

  logic                   memreq_val_M;
  logic                   memreq_rdy_M;
  logic [c_req_nbits-1:0] memreq_msg_M;

  vc_Queue
  #(
    .p_type      (`VC_QUEUE_PIPE),
    .p_msg_nbits (c_req_nbits),
    .p_num_msgs  (1)
  )
  memreq_queue
  (
    .clk     (clk),
    .reset   (reset),
    .enq_val (memreq_val),
    .enq_rdy (memreq_rdy),
    .enq_msg (memreq_msg),
    .deq_val (memreq_val_M),
    .deq_rdy (memreq_rdy_M),
    .deq_msg (memreq_msg_M)
  );

  //----------------------------------------------------------------------
  // Unpack the request messages
  //----------------------------------------------------------------------

  logic [c_req_type_nbits-1:0]   memreq_msg_type_M;
  logic [c_req_opaque_nbits-1:0] memreq_msg_opaque_M;
  logic [c_req_addr_nbits-1:0]   memreq_msg_addr_M;
  logic [c_req_len_nbits-1:0]    memreq_msg_len_M;
  logic [c_req_data_nbits-1:0]   memreq_msg_data_M;

  vc_MemReqMsgUnpack#(o,a,d) memreq_msg_unpack
  (
    .msg    (memreq_msg_M),
    .type_  (memreq_msg_type_M),
    .opaque (memreq_msg_opaque_M),
    .addr   (memreq_msg_addr_M),
    .len    (memreq_msg_len_M),
    .data   (memreq_msg_data_M)
  );

  //----------------------------------------------------------------------
  // Actual memory array
  //----------------------------------------------------------------------

  logic [p_data_nbits-1:0] m[c_num_blocks-1:0];

  //----------------------------------------------------------------------
  // Handle request and create response
  //----------------------------------------------------------------------

  // Handle case where length is zero which actually represents a full
  // width access.

  logic [c_req_len_nbits:0] memreq_msg_len_modified_M;
  assign memreq_msg_len_modified_M
    = ( memreq_msg_len_M == 0 ) ? (c_req_data_nbits/8)
    :                              memreq_msg_len_M;

  // Caculate the physical byte address for the request. Notice that we
  // truncate the higher order bits that are beyond the size of the
  // physical memory.

  logic [c_physical_addr_nbits-1:0] physical_byte_addr_M;
  assign physical_byte_addr_M = memreq_msg_addr_M[c_physical_addr_nbits-1:0];

  // Cacluate the block address and block offset

  logic [c_physical_block_addr_nbits-1:0] physical_block_addr_M;
  assign physical_block_addr_M = physical_byte_addr_M/c_data_byte_nbits;

  logic [c_block_offset_nbits-1:0] block_offset_M;
  assign block_offset_M = physical_byte_addr_M[c_block_offset_nbits-1:0];

  // Read the data

  logic [p_data_nbits-1:0] read_block_M;
  assign read_block_M = m[physical_block_addr_M];

  logic [c_resp_data_nbits-1:0] read_data_M;
  assign read_data_M = read_block_M >> (block_offset_M*8);

  // Write the data if required. This is a sequential always block so
  // that the write happens on the next edge.

  logic write_en_M;
  assign write_en_M = memreq_val_M &&
         ( memreq_msg_type_M == c_write || memreq_msg_type_M == c_write_init );

  // Note: amos need to happen once, so we only enable the amo transaction
  // when both val and rdy is high

  logic amo_en_M;
  assign amo_en_M = memreq_val_M && memreq_rdy_M &&
                                  ( memreq_msg_type_M == c_amo_and
                                 || memreq_msg_type_M == c_amo_add
                                 || memreq_msg_type_M == c_amo_or  );

  integer wr_i;

  // We use this variable to keep track of whether or not we have already
  // cleared the memory. Otherwise if the clear signal is high for
  // multiple cycles we will do the expensive reset multiple times. We
  // initialize this to one since by default when the simulation starts
  // the memory is already reset to X's.

  integer memory_cleared = 1;

  always_ff @( posedge clk ) begin

    // We clear all of the test memory to X's on mem_clear. As mentioned
    // above, this only happens if we clear a test memory more than once.
    // This is useful when we are reusing a memory for many tests to
    // avoid writes from one test "leaking" into a later test -- this
    // might possible cause a test to pass when it should not because the
    // test is using data from an older test.

    if ( mem_clear ) begin
      if ( !memory_cleared ) begin
        memory_cleared = 1;
        for ( wr_i = 0; wr_i < c_num_blocks; wr_i = wr_i + 1 ) begin
          m[wr_i] <= {p_data_nbits{1'bx}};
        end
      end
    end

    else if ( !reset ) begin
      memory_cleared = 0;

      if ( write_en_M ) begin
        for ( wr_i = 0; wr_i < memreq_msg_len_modified_M; wr_i = wr_i + 1 ) begin
          m[physical_block_addr_M][ (block_offset_M*8) + (wr_i*8) +: 8 ] <= memreq_msg_data_M[ (wr_i*8) +: 8 ];
        end
      end

      if ( amo_en_M ) begin
        case ( memreq_msg_type_M )
          c_amo_add: m[physical_block_addr_M] <= memreq_msg_data_M + read_data_M;
          c_amo_and: m[physical_block_addr_M] <= memreq_msg_data_M & read_data_M;
          c_amo_or : m[physical_block_addr_M] <= memreq_msg_data_M | read_data_M;
        endcase
      end

    end

  end

  //----------------------------------------------------------------------
  // Pack the response message
  //----------------------------------------------------------------------

  logic [c_resp_nbits-1:0] memresp_msg_M;

  vc_MemRespMsgPack#(o,d) memresp_msg_pack
  (
    .type_  (memreq_msg_type_M),
    .opaque (memreq_msg_opaque_M),
    .len    (memreq_msg_len_M),
    .data   (read_data_M),
    .msg    (memresp_msg_M)
  );

  //----------------------------------------------------------------------
  // Memory response buffers
  //----------------------------------------------------------------------
  // We use bypass queues here since in general we want our larger
  // modules to use registered inputs. By using a pipe queues at the
  // inputs and a bypass queue at the output we cut and combinational
  // paths through the test memory (helping to avoid combinational loops)
  // and also preserve our registered input policy.

  vc_Queue
  #(
    .p_type      (`VC_QUEUE_BYPASS),
    .p_msg_nbits (c_resp_nbits),
    .p_num_msgs  (1)
  )
  memresp_queue
  (
    .clk     (clk),
    .reset   (reset),
    .enq_val (memreq_val_M),
    .enq_rdy (memreq_rdy_M),
    .enq_msg (memresp_msg_M),
    .deq_val (memresp_val),
    .deq_rdy (memresp_rdy),
    .deq_msg (memresp_msg)
  );

  //----------------------------------------------------------------------
  // General assertions
  //----------------------------------------------------------------------

  // val/rdy signals should never be x's

  always_ff @( posedge clk ) begin
    if ( !reset ) begin
      `VC_ASSERT_NOT_X( memreq_val  );
      `VC_ASSERT_NOT_X( memresp_rdy );
    end
  end

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------

  vc_MemReqMsgTrace#(o,a,d) memreq_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (memreq_val),
    .rdy   (memreq_rdy),
    .msg   (memreq_msg)
  );

  vc_MemRespMsgTrace#(o,d) memresp_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (memresp_val),
    .rdy   (memresp_rdy),
    .msg   (memresp_msg)
  );

  `VC_TRACE_BEGIN
  begin

    memreq_trace.trace( trace_str );

    vc_trace.append_str( trace_str, "()" );

    memresp_trace.trace( trace_str );

  end
  `VC_TRACE_END

endmodule

`endif /* VC_TEST_MEM_1PORT_V */

