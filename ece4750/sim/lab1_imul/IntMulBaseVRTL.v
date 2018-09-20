//========================================================================
// Integer Multiplier Fixed-Latency Implementation
//========================================================================

`ifndef LAB1_IMUL_INT_MUL_BASE_V
`define LAB1_IMUL_INT_MUL_BASE_V

`include "vc/trace.v"

// ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// Define datapath and control unit here.
// '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

//========================================================================
// Integer Multiplier Fixed-Latency Implementation
//========================================================================

module lab1_imul_IntMulBaseVRTL
(
  input  logic        clk,
  input  logic        reset,

  input  logic        req_val,
  output logic        req_rdy,
  input  logic [63:0] req_msg,

  output logic        resp_val,
  input  logic        resp_rdy,
  output logic [31:0] resp_msg
);

  // ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // Instantiate datapath and control models here and then connect them
  // together.
  // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  
  logic [5:0] bit_count;
  
  logic [31:0] result_reg;
  logic [31:0] b_reg;
  logic [31:0] a_reg;
  
  logic data_mux_sel;
  logic result_mux_sel;
  logic add_mux_sel;
  
  logic [31:0] result_adder;
  logic [31:0] a_shift;
  logic [31:0] b_shift;
  
  typedef enum logic [$clog2(4)-1:0] {
    STATE_IDLE,
    STATE_CALC,
    STATE_DONE
  } state_t;
  
  state_t s_cur, s_next; 
  
  assign result_adder = result_reg + a_reg;
  assign a_shift = a_reg << 1;
  assign b_shift = b_reg >>> 1;
  assign add_mux_sel = ~b_reg[0];

  
  always_ff @(posedge(clk)) begin
    if (reset) begin
      s_cur <= STATE_IDLE;
    end else begin
      s_cur <= s_next;
    end
  
    b_reg <= (data_mux_sel) ? req_msg[31:0] : b_shift;
    a_reg <= (data_mux_sel) ? req_msg[63:32] : a_shift;

    result_reg <= (result_mux_sel) ? 0 : (add_mux_sel) ? result_reg : result_adder;


    bit_count <= (s_cur == STATE_CALC) ? bit_count+1 : 0;     
  end 


  always_comb begin
    case (s_cur)
      STATE_CALC: begin
        req_rdy = 0;
        resp_val = 0;
        resp_msg = result_reg;
        data_mux_sel = 0;
        result_mux_sel = 0;
      end
      STATE_DONE: begin
        req_rdy = 0;
        resp_val = 1;
        data_mux_sel = 0;
        result_mux_sel = 0;
        resp_msg = result_reg;
      end
      default: begin 
        req_rdy = 1;
        resp_val = 0;
        resp_msg = 0;
        data_mux_sel = 1;
        result_mux_sel = 1;
      end
    endcase
  end

  
  always_comb begin 
    case (s_cur)
      STATE_CALC: s_next = (bit_count < 6'd32) ? STATE_CALC : STATE_DONE;
      STATE_DONE: s_next = (resp_rdy) ? STATE_IDLE : STATE_DONE;
      default: s_next = (req_val) ? STATE_CALC : STATE_IDLE;
    endcase
  end
  
  //----------------------------------------------------------------------
  // Line Tracing
  //----------------------------------------------------------------------

  `ifndef SYNTHESIS

  logic [`VC_TRACE_NBITS-1:0] str;
  `VC_TRACE_BEGIN
  begin

    $sformat( str, "%x", req_msg );
    vc_trace.append_val_rdy_str( trace_str, req_val, req_rdy, str );

    vc_trace.append_str( trace_str, "(" );

    // ''' LAB TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
    // Add additional line tracing using the helper tasks for
    // internal state including the current FSM state.
    // '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    $sformat( str, "a_reg: %x ; ", a_reg );
    vc_trace.append_str( trace_str, str );
    $sformat( str, "b_reg %x ; ", b_reg );
    vc_trace.append_str( trace_str, str );
    $sformat( str, "result_reg %x ; ", result_reg );
    vc_trace.append_str( trace_str, str );
    

    vc_trace.append_str( trace_str, ")" );

    $sformat( str, "%x", resp_msg );
    vc_trace.append_val_rdy_str( trace_str, resp_val, resp_rdy, str );

  end
  `VC_TRACE_END

  `endif /* SYNTHESIS */

endmodule

`endif /* LAB1_IMUL_INT_MUL_BASE_V */

