//========================================================================
// vc-TestNet: Test Network
//========================================================================

`ifndef VC_TEST_NET_V
`define VC_TEST_NET_V

`include "vc/net-msgs.v"
`include "vc/arbiters.v"
`include "vc/queues.v"
`include "vc/param-utils.v"
`include "vc/trace.v"

module vc_TestNet
#(
  parameter p_num_ports      = 4,
  parameter p_queue_num_msgs = 4,
  parameter p_payload_nbits  = 32,
  parameter p_opaque_nbits   = 3,
  parameter p_srcdest_nbits  = 3,

  // Shorter names, not to be set from outside the module
  parameter p = p_payload_nbits,
  parameter o = p_opaque_nbits,
  parameter s = p_srcdest_nbits,

  parameter c_net_msg_nbits = `VC_NET_MSG_NBITS(p,o,s)
)
(
  input  logic clk,
  input  logic reset,

  input  logic [`VC_PORT_PICK_NBITS(1,p_num_ports)-1:0]               in_val,
  output logic [`VC_PORT_PICK_NBITS(1,p_num_ports)-1:0]               in_rdy,
  input  logic [`VC_PORT_PICK_NBITS(c_net_msg_nbits,p_num_ports)-1:0] in_msg,


  output logic [`VC_PORT_PICK_NBITS(1,p_num_ports)-1:0]               out_val,
  input  logic [`VC_PORT_PICK_NBITS(1,p_num_ports)-1:0]               out_rdy,
  output logic [`VC_PORT_PICK_NBITS(c_net_msg_nbits,p_num_ports)-1:0] out_msg
);

  // deq wires are the wires out of the input queues

  logic  [`VC_PORT_PICK_NBITS(1,p_num_ports)-1:0]               deq_val;
  logic  [`VC_PORT_PICK_NBITS(1,p_num_ports)-1:0]               deq_rdy;
  logic  [`VC_PORT_PICK_NBITS(c_net_msg_nbits,p_num_ports)-1:0] deq_msg;

  logic [`VC_PORT_PICK_NBITS(s,p_num_ports)-1:0] dests;
  logic [p_num_ports*p_num_ports-1:0] in_rdy_arr;

  // net string which is used to print the line tracing

  logic [(p_num_ports*6*8)-1:0] net_str;

  genvar in;
  genvar out;

  generate
  for ( in = 0; in < p_num_ports; in = in + 1 ) begin: IN_QUEUE

    vc_Queue
    #(
      .p_type      (`VC_QUEUE_NORMAL),
      .p_msg_nbits (c_net_msg_nbits),
      .p_num_msgs  (p_queue_num_msgs)
    )
    in_queue
    (
      .clk    (clk),
      .reset  (reset),

      .enq_val (in_val[`VC_PORT_PICK_FIELD(1,in)]),
      .enq_rdy (in_rdy[`VC_PORT_PICK_FIELD(1,in)]),
      .enq_msg (in_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,in)]),

      .deq_val (deq_val[`VC_PORT_PICK_FIELD(1,in)]),
      .deq_rdy (deq_rdy[`VC_PORT_PICK_FIELD(1,in)]),
      .deq_msg (deq_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,in)])
    );

    logic                        in_queue_deq_val;
    logic                        in_queue_deq_rdy;
    logic [c_net_msg_nbits-1:0]  in_queue_deq_msg;

    assign in_queue_deq_val = deq_val[`VC_PORT_PICK_FIELD(1,in)];
    assign in_queue_deq_rdy = deq_rdy[`VC_PORT_PICK_FIELD(1,in)];
    assign in_queue_deq_msg = deq_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,in)];

    // line tracing-related arb and net str
    logic [6*8-1:0] in_queue_str;
    assign net_str[`VC_PORT_PICK_FIELD(6*8,p_num_ports-in-1)] =
                                                        in_queue_str;

    always_comb begin
      if ( in_queue_deq_val && in_queue_deq_rdy )
        $sformat( in_queue_str, "(%x>%x)",
                  in_queue_deq_msg[`VC_NET_MSG_OPAQUE_FIELD(p,o,s)],
                  in_queue_deq_msg[`VC_NET_MSG_DEST_FIELD(p,o,s)] );
      else if ( !in_queue_deq_val && in_queue_deq_rdy )
        $sformat( in_queue_str, "(    )" );
      else if ( !in_queue_deq_val && !in_queue_deq_rdy )
        $sformat( in_queue_str, "(.   )" );
      else if ( in_queue_deq_val && !in_queue_deq_rdy )
        $sformat( in_queue_str, "(#   )" );

    end

  end
  endgenerate

  generate
  for ( in = 0; in < p_num_ports; in = in + 1 ) begin: MSG_UNPACK

    vc_NetMsgUnpack #(p,o,s) msg_unpack
    (
      .msg    (deq_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,in)]),
      .dest   (dests[`VC_PORT_PICK_FIELD(s,in)])
    );
  end
  endgenerate

  generate
  for ( out = 0; out < p_num_ports; out = out + 1 ) begin: ARB_OUT

    logic [p_num_ports-1:0] reqs;
    logic [p_num_ports-1:0] grants;

    vc_RoundRobinArb #(p_num_ports) arb
    (
      .clk      (clk),
      .reset    (reset),
      .reqs     (reqs),
      .grants   (grants)
    );

    // out val is high if there has been any requests (hence grants)
    assign out_val[out] = | grants;


    for ( in = 0; in < p_num_ports; in = in + 1) begin: ARB_IN
      // we request a port if the in is valid and the destination is for
      // this output port
      assign reqs[in] = ( deq_val[in] &&
                dests[`VC_PORT_PICK_FIELD(s,in)] == out );

    end

    // we circuit-connect the out msg to the granted in msg
    logic [31:0] i;

    // binary encoded grants signal
    logic [3:0] grants_bin;
    logic [c_net_msg_nbits-1:0] arb_out_msg;
    assign out_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,out)] = arb_out_msg;
    logic [c_net_msg_nbits-1:0] arb_in_msg0;
    logic [c_net_msg_nbits-1:0] arb_in_msg1;

    assign arb_in_msg0 = deq_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,0)];
    assign arb_in_msg1 = deq_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,1)];

    //// line tracing-related arb and net str
    //logic [5*8-1:0] arb_str;
    //assign net_str[`VC_PORT_PICK_FIELD(5*8,p_num_ports-out-1)] = arb_str;

    always_comb begin
      arb_out_msg = 0;
      grants_bin = 0;
      for ( i = 0; i < p_num_ports; i = i + 1 ) begin
        in_rdy_arr[out + i*p_num_ports] = (grants[i] && out_rdy[out]);
        if ( ( 1 << i ) & grants ) begin
          arb_out_msg = arb_out_msg |
                deq_msg[`VC_PORT_PICK_FIELD(c_net_msg_nbits,i)];
          grants_bin = i;
        end
      end

      //if ( grants == 0 ) begin
      //  $sformat( arb_str, "(   )" );
      //end else begin
      //  $sformat( arb_str, "(%x>%x)", grants_bin, out );
      //end
    end

  end
  endgenerate

  logic [31:0] i;
  always_comb begin
    for ( i = 0; i < p_num_ports; i = i + 1 ) begin
      deq_rdy[i] = | in_rdy_arr[`VC_PORT_PICK_FIELD(p_num_ports,i)];
    end
  end

  //----------------------------------------------------------------------
  // Line Tracing
  //----------------------------------------------------------------------

  `VC_TRACE_BEGIN
  begin
    vc_trace.append_str( trace_str, net_str );
  end
  `VC_TRACE_END


endmodule

`endif

