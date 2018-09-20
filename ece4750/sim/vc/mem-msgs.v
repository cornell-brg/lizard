//========================================================================
// vc-mem-msgs : Memory Request/Response Messages
//========================================================================
// The memory request/response messages are used to interact with various
// memories. They are parameterized by the number of bits in the address,
// data, and opaque field.

`ifndef VC_MEM_MSGS_V
`define VC_MEM_MSGS_V

`include "vc/trace.v"

//========================================================================
// Memory Request Message
//========================================================================
// Memory request messages can either be for a read or write. Read
// requests include an opaque field, the address, and the number of bytes
// to read, while write requests include an opaque field, the address,
// the number of bytes to write, and the actual data to write.
//
// Message Format:
//
//    3b    p_opaque_nbits  p_addr_nbits       calc   p_data_nbits
//  +------+---------------+------------------+------+------------------+
//  | type | opaque        | addr             | len  | data             |
//  +------+---------------+------------------+------+------------------+
//
// The message type is parameterized by the number of bits in the opaque
// field, address field, and data field. Note that the size of the length
// field is caclulated from the number of bits in the data field, and
// that the length field is expressed in _bytes_. If the value of the
// length field is zero, then the read or write should be for the full
// width of the data field.
//
// For example, if the opaque field is 8 bits, the address is 32 bits and
// the data is also 32 bits, then the message format is as follows:
//
//   76  74 73           66 65              34 33  32 31               0
//  +------+---------------+------------------+------+------------------+
//  | type | opaque        | addr             | len  | data             |
//  +------+---------------+------------------+------+------------------+
//
// The length field is two bits. A length value of one means read or write
// a single byte, a length value of two means read or write two bytes, and
// so on. A length value of zero means read or write all four bytes. Note
// that not all memories will necessarily support any alignment and/or any
// value for the length field.
//
// The opaque field is reserved for use by a specific implementation. All
// memories should guarantee that every response includes the opaque
// field corresponding to the request that generated the response.

//------------------------------------------------------------------------
// Memory Request Struct: Using a packed struct to represent the message
//------------------------------------------------------------------------
typedef struct packed {
  logic [2:0]  type_;
  logic [7:0]  opaque;
  logic [31:0] addr;
  logic [1:0]  len;
  logic [31:0] data;
} mem_req_4B_t;

typedef struct packed {
  logic [2:0]  type_;
  logic [7:0]  opaque;
  logic [31:0] addr;
  logic [3:0]  len;
  logic [127:0] data;
} mem_req_16B_t;

// memory request type values
`define VC_MEM_REQ_MSG_TYPE_READ     3'd0
`define VC_MEM_REQ_MSG_TYPE_WRITE    3'd1

// write no-refill
`define VC_MEM_REQ_MSG_TYPE_WRITE_INIT 3'd2
`define VC_MEM_REQ_MSG_TYPE_AMO_ADD    3'd3
`define VC_MEM_REQ_MSG_TYPE_AMO_AND    3'd4
`define VC_MEM_REQ_MSG_TYPE_AMO_OR     3'd5
`define VC_MEM_REQ_MSG_TYPE_X          3'dx

//------------------------------------------------------------------------
// Memory Request Message: Trace message
//------------------------------------------------------------------------

module vc_MemReqMsg4BTrace
(
  input logic         clk,
  input logic         reset,
  input logic         val,
  input logic         rdy,
  input mem_req_4B_t  msg
);

  logic [2:0]   type_;
  assign type_  = msg.type_;
  logic [7:0]   opaque;
  assign opaque = msg.opaque;
  logic [31:0]  addr;
  assign addr   = msg.addr;
  logic [1:0]   len;
  assign len    = msg.len;
  logic [31:0]  data;
  assign data   = msg.data;

  // Short names

  localparam c_msg_nbits = $bits(mem_req_4B_t);
  localparam c_read      = `VC_MEM_REQ_MSG_TYPE_READ;
  localparam c_write     = `VC_MEM_REQ_MSG_TYPE_WRITE;
  localparam c_write_init  = `VC_MEM_REQ_MSG_TYPE_WRITE_INIT;

  // Line tracing

  logic [8*2-1:0] type_str;
  logic [`VC_TRACE_NBITS-1:0] str;

  `VC_TRACE_BEGIN
  begin

    // Convert type into a string

    if ( msg.type_ === `VC_MEM_REQ_MSG_TYPE_X )
      type_str = "xx";
    else begin
      case ( msg.type_ )
        c_read     : type_str = "rd";
        c_write    : type_str = "wr";
        c_write_init : type_str = "wn";
        default    : type_str = "??";
      endcase
    end

    // Put together the trace string

    if ( vc_trace.level == 1 ) begin
      $sformat( str, "%s", type_str );
    end
    else if ( vc_trace.level == 2 ) begin
      $sformat( str, "%s:%x", type_str, msg.addr );
    end
    else if ( vc_trace.level == 3 ) begin
      if ( type_ == c_read ) begin
        $sformat( str, "%s:%x:%x %s", type_str, msg.opaque, msg.addr,
                  {8{" "}} );
      end
      else
        $sformat( str, "%s:%x:%x:%x", type_str, msg.opaque, msg.addr, msg.data );
    end

    // Trace with val/rdy signals

    vc_trace.append_val_rdy_str( trace_str, val, rdy, str );

  end
  `VC_TRACE_END

endmodule

module vc_MemReqMsg16BTrace
(
  input logic         clk,
  input logic         reset,
  input logic         val,
  input logic         rdy,
  input mem_req_16B_t  msg
);

  logic [2:0]   type_;
  assign type_  = msg.type_;
  logic [7:0]   opaque;
  assign opaque = msg.opaque;
  logic [31:0]  addr;
  assign addr   = msg.addr;
  logic [3:0]   len;
  assign len    = msg.len;
  logic [127:0]  data;
  assign data   = msg.data;

  // Short names

  localparam c_msg_nbits = $bits(mem_req_16B_t);
  localparam c_read      = `VC_MEM_REQ_MSG_TYPE_READ;
  localparam c_write     = `VC_MEM_REQ_MSG_TYPE_WRITE;
  localparam c_write_init  = `VC_MEM_REQ_MSG_TYPE_WRITE_INIT;

  // Line tracing

  logic [8*2-1:0] type_str;
  logic [`VC_TRACE_NBITS-1:0] str;

  `VC_TRACE_BEGIN
  begin

    // Convert type into a string

    if ( msg.type_ === `VC_MEM_REQ_MSG_TYPE_X )
      type_str = "xx";
    else begin
      case ( msg.type_ )
        c_read     : type_str = "rd";
        c_write    : type_str = "wr";
        c_write_init : type_str = "wn";
        default    : type_str = "??";
      endcase
    end

    // Put together the trace string

    if ( vc_trace.level == 1 ) begin
      $sformat( str, "%s", type_str );
    end
    else if ( vc_trace.level == 2 ) begin
      $sformat( str, "%s:%x", type_str, msg.addr );
    end
    else if ( vc_trace.level == 3 ) begin
      if ( type_ == c_read ) begin
        $sformat( str, "%s:%x:%x %s", type_str, msg.opaque, msg.addr,
                  {32{" "}} );
      end
      else
        $sformat( str, "%s:%x:%x:%x", type_str, msg.opaque, msg.addr, msg.data );
    end

    // Trace with val/rdy signals

    vc_trace.append_val_rdy_str( trace_str, val, rdy, str );

  end
  `VC_TRACE_END

endmodule

//========================================================================
// Memory Response Message
//========================================================================
// Memory request messages can either be for a read or write. Read
// responses include an opaque field, the actual data, and the number of
// bytes, while write responses currently include just the opaque field.
//
// Message Format:
//
//    3b    p_opaque_nbits   2b    calc   p_data_nbits
//  +------+---------------+------+------+------------------+
//  | type | opaque        | test | len  | data             |
//  +------+---------------+------+------+------------------+
//
// The message type is parameterized by the number of bits in the opaque
// field and data field. Note that the size of the length field is
// caclulated from the number of bits in the data field, and that the
// length field is expressed in _bytes_. If the value of the length field
// is zero, then the read or write should be for the full width of the
// data field.
//
// For example, if the opaque field is 8 bits and the data is 32 bits,
// then the message format is as follows:
//
//   46  44 43           36 35  34 33  32 31               0
//  +------+---------------+------+------+------------------+
//  | type | opaque        | test | len  | data             |
//  +------+---------------+------+------+------------------+
//
// The length field is two bits. A length value of one means one byte was
// read, a length value of two means two bytes were read, and so on. A
// length value of zero means all four bytes were read. Note that not all
// memories will necessarily support any alignment and/or any value for
// the length field.
//
// The opaque field is reserved for use by a specific implementation. All
// memories should guarantee that every response includes the opaque
// field corresponding to the request that generated the response.

//------------------------------------------------------------------------
// Memory Request Struct: Using a packed struct to represent the message
//------------------------------------------------------------------------
typedef struct packed {
  logic [2:0]  type_;
  logic [7:0]  opaque;
  logic [1:0]  test;
  logic [1:0]  len;
  logic [31:0] data;
} mem_resp_4B_t;

typedef struct packed {
  logic [2:0]  type_;
  logic [7:0]  opaque;
  logic [1:0]  test;
  logic [3:0]  len;
  logic [127:0] data;
} mem_resp_16B_t;

// Values for the type field

`define VC_MEM_RESP_MSG_TYPE_READ     3'd0
`define VC_MEM_RESP_MSG_TYPE_WRITE    3'd1

// write no-refill
`define VC_MEM_RESP_MSG_TYPE_WRITE_INIT 3'd2
`define VC_MEM_RESP_MSG_TYPE_AMO_ADD    3'd3
`define VC_MEM_RESP_MSG_TYPE_AMO_AND    3'd4
`define VC_MEM_RESP_MSG_TYPE_AMO_OR     3'd5
`define VC_MEM_RESP_MSG_TYPE_X          3'dx

//------------------------------------------------------------------------
// Memory Response Message: Trace message
//------------------------------------------------------------------------

module vc_MemRespMsg4BTrace
(
  input logic          clk,
  input logic          reset,
  input logic          val,
  input logic          rdy,
  input mem_resp_4B_t  msg
);

  // unpack message fields -- makes them visible in gtkwave
  logic [2:0]   type_;
  assign type_  = msg.type_;
  logic [7:0]   opaque;
  assign opaque = msg.opaque;
  logic [1:0]   test;
  assign test   = msg.test;
  logic [1:0]   len;
  assign len    = msg.len;
  logic [31:0]  data;
  assign data   = msg.data;

  // Short names

  localparam c_msg_nbits  = $bits(mem_resp_4B_t);
  localparam c_read       = `VC_MEM_RESP_MSG_TYPE_READ;
  localparam c_write      = `VC_MEM_RESP_MSG_TYPE_WRITE;
  localparam c_write_init = `VC_MEM_RESP_MSG_TYPE_WRITE_INIT;

  // Line tracing

  logic [8*2-1:0] type_str;
  logic [`VC_TRACE_NBITS-1:0] str;

  `VC_TRACE_BEGIN
  begin

    // Convert type into a string

    if ( type_ === `VC_MEM_RESP_MSG_TYPE_X )
      type_str = "xx";
    else begin
      case ( type_ )
        c_read       : type_str = "rd";
        c_write      : type_str = "wr";
        c_write_init : type_str = "wn";
        default      : type_str = "??";
      endcase
    end

    // Put together the trace string

    if ( (vc_trace.level == 1) || (vc_trace.level == 2) ) begin
      $sformat( str, "%s", type_str );
    end
    else if ( vc_trace.level == 3 ) begin
      if ( type_ == c_write || type_ == c_write_init ) begin
        $sformat( str, "%s:%x %s", type_str, opaque,
                  {8{" "}} );
      end
      else
        $sformat( str, "%s:%x:%x", type_str, opaque, data );
    end

    // Trace with val/rdy signals

    vc_trace.append_val_rdy_str( trace_str, val, rdy, str );

  end
  `VC_TRACE_END

endmodule

module vc_MemRespMsg16BTrace
(
  input logic          clk,
  input logic          reset,
  input logic          val,
  input logic          rdy,
  input mem_resp_16B_t msg
);

  // unpack message fields -- makes them visible in gtkwave
  logic [2:0]   type_;
  assign type_  = msg.type_;
  logic [7:0]   opaque;
  assign opaque = msg.opaque;
  logic [1:0]   test;
  assign test   = msg.test;
  logic [3:0]   len;
  assign len    = msg.len;
  logic [127:0] data;
  assign data   = msg.data;

  // Short names

  localparam c_msg_nbits  = $bits(mem_resp_16B_t);
  localparam c_read       = `VC_MEM_RESP_MSG_TYPE_READ;
  localparam c_write      = `VC_MEM_RESP_MSG_TYPE_WRITE;
  localparam c_write_init = `VC_MEM_RESP_MSG_TYPE_WRITE_INIT;

  // Line tracing

  logic [8*2-1:0] type_str;
  logic [`VC_TRACE_NBITS-1:0] str;

  `VC_TRACE_BEGIN
  begin

    // Convert type into a string

    if ( type_ === `VC_MEM_RESP_MSG_TYPE_X )
      type_str = "xx";
    else begin
      case ( type_ )
        c_read       : type_str = "rd";
        c_write      : type_str = "wr";
        c_write_init : type_str = "wn";
        default      : type_str = "??";
      endcase
    end

    // Put together the trace string

    if ( (vc_trace.level == 1) || (vc_trace.level == 2) ) begin
      $sformat( str, "%s", type_str );
    end
    else if ( vc_trace.level == 3 ) begin
      if ( type_ == c_write || type_ == c_write_init ) begin
        $sformat( str, "%s:%x %s", type_str, opaque,
                  {32{" "}} );
      end
      else
        $sformat( str, "%s:%x:%x", type_str, opaque, data );
    end

    // Trace with val/rdy signals

    vc_trace.append_val_rdy_str( trace_str, val, rdy, str );

  end
  `VC_TRACE_END

endmodule

`endif /* VC_MEM_MSGS_V */

