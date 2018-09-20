//========================================================================
// Cache Request/Response Network
//========================================================================

`ifndef LAB5_MCORE_CACHE_NET_V
`define LAB5_MCORE_CACHE_NET_V

`include "vc/mem-msgs.v"
`include "vc/net-msgs.v"
`include "lab4_net/BusNetVRTL.v"
`include "lab5_mcore/MsgAdapters.v"

module lab5_mcore_CacheNetVRTL
(
  input  logic                            clk,
  input  logic                            reset,

  input  mem_req_4B_t  [c_num_ports-1:0] procreq_msg,
  input  logic         [c_num_ports-1:0] procreq_val,
  output logic         [c_num_ports-1:0] procreq_rdy,

  output mem_resp_4B_t [c_num_ports-1:0] procresp_msg,
  output logic         [c_num_ports-1:0] procresp_val,
  input  logic         [c_num_ports-1:0] procresp_rdy,

  output mem_req_4B_t  [c_num_ports-1:0] cachereq_msg,
  output logic         [c_num_ports-1:0] cachereq_val,
  input  logic         [c_num_ports-1:0] cachereq_rdy,

  input  mem_resp_4B_t [c_num_ports-1:0] cacheresp_msg,
  input  logic         [c_num_ports-1:0] cacheresp_val,
  output logic         [c_num_ports-1:0] cacheresp_rdy

);

  localparam c_num_ports = 4;

  net_hdr_t     [c_num_ports-1:0] procreq_net_msg_hdr;
  mem_req_4B_t  [c_num_ports-1:0] procreq_net_msg_payload;
  net_hdr_t     [c_num_ports-1:0] procresp_net_msg_hdr;
  mem_resp_4B_t [c_num_ports-1:0] procresp_net_msg_payload;
  net_hdr_t     [c_num_ports-1:0] cachereq_net_msg_hdr;
  mem_req_4B_t  [c_num_ports-1:0] cachereq_net_msg_payload;
  net_hdr_t     [c_num_ports-1:0] cacheresp_net_msg_hdr;
  mem_resp_4B_t [c_num_ports-1:0] cacheresp_net_msg_payload;

  genvar i;

  generate
    for ( i = 0; i < c_num_ports; i = i + 1 ) begin: ADAPTERS

      lab5_mcore_4BUpstreamMsgAdapter
      #(
        .p_single_bank (0)
      )
      u_adpt
      (
        .src_id              (i[1:0]),

        .memreq_msg          (procreq_msg[i]),
        .netreq_msg_hdr      (procreq_net_msg_hdr[i]),
        .netreq_msg_payload  (procreq_net_msg_payload[i]),

        .memresp_msg         (procresp_msg[i]),
        .netresp_msg_hdr     (procresp_net_msg_hdr[i]),
        .netresp_msg_payload (procresp_net_msg_payload[i])
      );

      lab5_mcore_4BDownstreamAdapter d_adpt
      (
        .src_id              (i[1:0]),

        .memreq_msg          (cachereq_msg[i]),
        .netreq_msg_hdr      (cachereq_net_msg_hdr[i]),
        .netreq_msg_payload  (cachereq_net_msg_payload[i]),

        .memresp_msg         (cacheresp_msg[i]),
        .netresp_msg_hdr     (cacheresp_net_msg_hdr[i]),
        .netresp_msg_payload (cacheresp_net_msg_payload[i])
      );

    end
  endgenerate

  // request network

  lab4_net_BusNetVRTL #($bits(mem_req_4B_t)) reqnet
  (
    .clk            (clk),
    .reset          (reset),

    .in_val         (procreq_val),
    .in_rdy         (procreq_rdy),
    .in_msg_hdr     (procreq_net_msg_hdr),
    .in_msg_payload (procreq_net_msg_payload),

    .out_val        (cachereq_val),
    .out_rdy        (cachereq_rdy),
    .out_msg_hdr    (cachereq_net_msg_hdr),
    .out_msg_payload(cachereq_net_msg_payload)
  );

  // response network

  lab4_net_BusNetVRTL #($bits(mem_resp_4B_t)) respnet
  (
    .clk            (clk),
    .reset          (reset),

    .in_val         (cacheresp_val),
    .in_rdy         (cacheresp_rdy),
    .in_msg_hdr     (cacheresp_net_msg_hdr),
    .in_msg_payload (cacheresp_net_msg_payload),

    .out_val        (procresp_val),
    .out_rdy        (procresp_rdy),
    .out_msg_hdr    (procresp_net_msg_hdr),
    .out_msg_payload(procresp_net_msg_payload)
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
