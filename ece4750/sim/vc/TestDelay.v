//========================================================================
// Verilog Components : Test (Fixed) Delay
//========================================================================
// We make the delay a actual input as opposed to a parameter to reduce
// the need to instantiate many different test harnesses in unit testing
// and to enable setting the delay from the command line in simulators.

`ifndef VC_TEST_DELAY_V
`define VC_TEST_DELAY_V

`include "vc/regs.v"
`include "vc/trace.v"

module vc_TestDelay
#(
  parameter p_msg_nbits = 1 // size of message in bits
)(
  input  logic                   clk,
  input  logic                   reset,

  // Delay input

  input  logic [31:0]            delay_amt,

  // Input interface

  input  logic                   in_val,
  output logic                   in_rdy,
  input  logic [p_msg_nbits-1:0] in_msg,

  // Output interface

  output logic                   out_val,
  input  logic                   out_rdy,
  output logic [p_msg_nbits-1:0] out_msg
);

  //----------------------------------------------------------------------
  // State
  //----------------------------------------------------------------------

  // Delay counter

  logic        delay_en;
  logic [31:0] delay_next;
  logic [31:0] delay;

  vc_EnResetReg#(32,32'b0) delay_reg
  (
    .clk   (clk),
    .reset (reset),
    .en    (delay_en),
    .d     (delay_next),
    .q     (delay)
  );

  //----------------------------------------------------------------------
  // Helper combinational logic
  //----------------------------------------------------------------------

  // The zero_cycle_delay signal is true when we can directly pass the
  // input message to the output interface without moving into the delay
  // state. This only happens when the input is valid, the output is
  // ready, and the delay amount is zero.

  logic zero_cycle_delay;
  assign zero_cycle_delay = in_val && out_rdy && (delay_amt == 0);

  //----------------------------------------------------------------------
  // State register
  //----------------------------------------------------------------------

  localparam c_state_sz    = 1;
  localparam c_state_idle  = 1'b0;
  localparam c_state_delay = 1'b1;

  logic [c_state_sz-1:0] state_next;
  logic [c_state_sz-1:0] state;

  always_ff @( posedge clk ) begin
    if ( reset ) begin
      state <= c_state_idle;
    end
    else begin
      state <= state_next;
    end
  end

  //----------------------------------------------------------------------
  // State transitions
  //----------------------------------------------------------------------

  always_comb begin

    // Default is to stay in the same state

    state_next = state;

    case ( state )

      // Move into delay state if a message arrives on the input
      // interface, except in the case when there is a zero cycle delay
      // (see definition of zero_cycle_delay signal above).

      c_state_idle:
        if ( in_val && !zero_cycle_delay ) begin
          state_next = c_state_delay;
        end

      // Move back into idle state once we have waited the correct number
      // of cycles and the output interface is ready so that we can
      // actually transfer the message.

      c_state_delay:
        if ( in_val && out_rdy && (delay == 0) ) begin
          state_next = c_state_idle;
        end

    endcase

  end

  //----------------------------------------------------------------------
  // State output
  //----------------------------------------------------------------------

  always_comb begin

    case ( state )

      c_state_idle:
      begin
        delay_en   = in_val && !zero_cycle_delay;
        delay_next = (delay_amt > 0) ? delay_amt - 1 : delay_amt;
        in_rdy     = out_rdy && (delay_amt == 0);
        out_val    = in_val  && (delay_amt == 0);
      end

      c_state_delay:
      begin
        delay_en   = (delay > 0);
        delay_next = delay - 1;
        in_rdy     = out_rdy && (delay == 0);
        out_val    = in_val  && (delay == 0);
      end

      default:
      begin
        delay_en   = 1'bx;
        delay_next = 32'bx;
        in_rdy     = 1'bx;
        out_val    = 1'bx;
      end

    endcase

  end

  //----------------------------------------------------------------------
  // Other combinational logic
  //----------------------------------------------------------------------

  // Directly connect output msg bits to input msg bits, only when out_val
  // is high

  assign out_msg = out_val ? in_msg : 'hx;

  //----------------------------------------------------------------------
  // Assertions
  //----------------------------------------------------------------------

  always_ff @( posedge clk ) begin
    if ( !reset ) begin
      `VC_ASSERT_NOT_X( delay_amt );
      `VC_ASSERT_NOT_X( in_val    );
      `VC_ASSERT_NOT_X( in_rdy    );
      `VC_ASSERT_NOT_X( out_val   );
      `VC_ASSERT_NOT_X( out_rdy   );
    end
  end

  //----------------------------------------------------------------------
  // Line Tracing
  //----------------------------------------------------------------------

  logic [`VC_TRACE_NBITS_TO_NCHARS(p_msg_nbits)*8-1:0] msg_str;

  `VC_TRACE_BEGIN
  begin

    $sformat( msg_str, "%x", in_msg );
    vc_trace.append_val_rdy_str( trace_str, in_val,  in_rdy,  msg_str  );

    vc_trace.append_str( trace_str, "|" );

    $sformat( msg_str, "%x", out_msg );
    vc_trace.append_val_rdy_str( trace_str, out_val, out_rdy, msg_str );

  end
  `VC_TRACE_END

endmodule

`endif /* VC_TEST_DELAY_V */

