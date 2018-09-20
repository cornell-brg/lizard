//========================================================================
// Memory Request/Response Network
//========================================================================

`ifndef LAB5_MCORE_MEM_NET_V
`define LAB5_MCORE_MEM_NET_V

`include "vc/mem-msgs.v"
`include "vc/net-msgs.v"
`include "lab4_net/BusNetVRTL.v"
`include "lab5_mcore/MsgAdapters.v"

module lab5_mcore_MemNetVRTL
(
  input  logic                            clk,
  input  logic                            reset,

  input  mem_req_16B_t  [c_num_ports-1:0] memreq_msg,
  input  logic          [c_num_ports-1:0] memreq_val,
  output logic          [c_num_ports-1:0] memreq_rdy,

  output mem_resp_16B_t [c_num_ports-1:0] memresp_msg,
  output logic          [c_num_ports-1:0] memresp_val,
  input  logic          [c_num_ports-1:0] memresp_rdy,

  output mem_req_16B_t  [c_num_ports-1:0] mainmemreq_msg,
  output logic          [c_num_ports-1:0] mainmemreq_val,
  input  logic          [c_num_ports-1:0] mainmemreq_rdy,

  input  mem_resp_16B_t [c_num_ports-1:0] mainmemresp_msg,
  input  logic          [c_num_ports-1:0] mainmemresp_val,
  output logic          [c_num_ports-1:0] mainmemresp_rdy

);

  localparam c_num_ports = 4;

  net_hdr_t      [c_num_ports-1:0] memreq_net_msg_hdr;
  mem_req_16B_t  [c_num_ports-1:0] memreq_net_msg_payload;
  net_hdr_t      [c_num_ports-1:0] memresp_net_msg_hdr;
  mem_resp_16B_t [c_num_ports-1:0] memresp_net_msg_payload;
  net_hdr_t      [c_num_ports-1:0] mainmemreq_net_msg_hdr;
  mem_req_16B_t  [c_num_ports-1:0] mainmemreq_net_msg_payload;
  net_hdr_t      [c_num_ports-1:0] mainmemresp_net_msg_hdr;
  mem_resp_16B_t [c_num_ports-1:0] mainmemresp_net_msg_payload;

  genvar i;

  generate
    for ( i = 0; i < c_num_ports; i = i + 1 ) begin: ADAPTERS

      lab5_mcore_16BUpstreamMsgAdapter
      #(
        .p_single_bank (1)
      )
      u_adpt
      (
        .src_id              (i[1:0]),

        .memreq_msg          (memreq_msg[i]),
        .netreq_msg_hdr      (memreq_net_msg_hdr[i]),
        .netreq_msg_payload  (memreq_net_msg_payload[i]),

        .memresp_msg         (memresp_msg[i]),
        .netresp_msg_hdr     (memresp_net_msg_hdr[i]),
        .netresp_msg_payload (memresp_net_msg_payload[i])
      );

      lab5_mcore_16BDownstreamAdapter d_adpt
      (
        .src_id              (i[1:0]),

        .memreq_msg          (mainmemreq_msg[i]),
        .netreq_msg_hdr      (mainmemreq_net_msg_hdr[i]),
        .netreq_msg_payload  (mainmemreq_net_msg_payload[i]),

        .memresp_msg         (mainmemresp_msg[i]),
        .netresp_msg_hdr     (mainmemresp_net_msg_hdr[i]),
        .netresp_msg_payload (mainmemresp_net_msg_payload[i])
      );

    end
  endgenerate

  // request network
  // Note that for 16B messages, we always connect a single memory to port 0
  // so we'll make sure the val and rdy signals for the other ports stay low
  lab4_net_BusNetVRTL #($bits(mem_req_16B_t)) reqnet
  (
    .clk            (clk),
    .reset          (reset),

    .in_val         (memreq_val),
    .in_rdy         (memreq_rdy),
    .in_msg_hdr     (memreq_net_msg_hdr),
    .in_msg_payload (memreq_net_msg_payload),

    .out_val        (mainmemreq_val),
    .out_rdy        (mainmemreq_rdy),
    .out_msg_hdr    (mainmemreq_net_msg_hdr),
    .out_msg_payload(mainmemreq_net_msg_payload)
  );

  // response network

  lab4_net_BusNetVRTL #($bits(mem_resp_16B_t)) respnet
  (
    .clk            (clk),
    .reset          (reset),

    .in_val         (mainmemresp_val),
    .in_rdy         (mainmemresp_rdy),
    .in_msg_hdr     (mainmemresp_net_msg_hdr),
    .in_msg_payload (mainmemresp_net_msg_payload),

    .out_val        (memresp_val),
    .out_rdy        (memresp_rdy),
    .out_msg_hdr    (memresp_net_msg_hdr),
    .out_msg_payload(memresp_net_msg_payload)
  );

  `VC_TRACE_BEGIN
  begin
    reqnet.line_trace( trace_str );
    vc_trace.append_str( trace_str, " >>> " );
    respnet.line_trace( trace_str );
  end
  `VC_TRACE_END
endmodule

`endif /* LAB5_MCORE_MEM_NET_V */
