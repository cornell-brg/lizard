//========================================================================
// Memory-Network message adapters
//========================================================================

`ifndef LAB5_MCORE_MEM_NET_MSG_ADAPTERS_V
`define LAB5_MCORE_MEM_NET_MSG_ADAPTERS_V

`include "vc/mem-msgs.v"
`include "vc/net-msgs.v"

module lab5_mcore_16BUpstreamMsgAdapter
#(
  // whether the network is single-bank (ie cache->mem)
  parameter p_single_bank = 0
)
(
  input  logic [c_net_srcdest_nbits-1:0] src_id,

  input  mem_req_16B_t                   memreq_msg,

  output net_hdr_t                       netreq_msg_hdr,
  output mem_req_16B_t                   netreq_msg_payload,

  output mem_resp_16B_t                  memresp_msg,

  input  net_hdr_t                       netresp_msg_hdr,
  input  mem_resp_16B_t                  netresp_msg_payload

);
  // memory-related localparams
  localparam c_mem_opaque_nbits = 8;

  // network-related localparams
  localparam c_net_opaque_nbits = 8;
  localparam c_net_srcdest_nbits = 2;

  // number of words in a cacheline
  localparam c_cacheline_nwords = 4;

  // shorter names for memory localparams
  localparam mo = c_mem_opaque_nbits;

  // shorter names for network localparams
  localparam ns = c_net_srcdest_nbits;

  // destination indexing from the memory address
  localparam c_dest_addr_lsb = 2 + $clog2(c_cacheline_nwords);

  // we use high bits of the opaque field to put the destination info
  // we re-pack the memory message with the new opaque field
  always_comb begin
    netreq_msg_payload = memreq_msg;
    netreq_msg_payload.opaque[mo-1 -: ns] = src_id[ns-1:0];
  end

  // build the header for the network message
  // Destination depends on whether this is single bank
  // If multi-bank, use bits from the memory address as the dest id
  assign netreq_msg_hdr.dest   = p_single_bank ? {c_net_srcdest_nbits{1'b0}}
                                   : memreq_msg.addr[c_dest_addr_lsb +: c_net_srcdest_nbits];
  assign netreq_msg_hdr.src    = src_id;
  assign netreq_msg_hdr.opaque = {c_net_opaque_nbits{1'b0}};

  // The bits of the opaque field that were used for tracking the resp
  // destination need to be zeroed out
  always_comb begin
    memresp_msg = netresp_msg_payload;
    memresp_msg.opaque[mo-1 -: ns] = {ns{1'b0}};
  end

endmodule

module lab5_mcore_4BUpstreamMsgAdapter
#(
  // whether the network is single-bank (ie cache->mem)
  parameter p_single_bank = 0
)
(
  input  logic [c_net_srcdest_nbits-1:0] src_id,

  input  mem_req_4B_t                    memreq_msg,

  output net_hdr_t                       netreq_msg_hdr,
  output mem_req_4B_t                    netreq_msg_payload,

  output mem_resp_4B_t                   memresp_msg,

  input  net_hdr_t                       netresp_msg_hdr,
  input  mem_resp_4B_t                   netresp_msg_payload

);
  // memory-related localparams
  localparam c_mem_opaque_nbits = 8;

  // network-related localparams
  localparam c_net_opaque_nbits = 8;
  localparam c_net_srcdest_nbits = 2;

  // number of words in a cacheline
  localparam c_cacheline_nwords = 4;

  // shorter names for memory localparams
  localparam mo = c_mem_opaque_nbits;

  // shorter names for network localparams
  localparam ns = c_net_srcdest_nbits;

  // destination indexing from the memory address
  localparam c_dest_addr_lsb = 2 + $clog2(c_cacheline_nwords);

  // we use high bits of the opaque field to put the destination info
  // we re-pack the memory message with the new opaque field
  always_comb begin
    netreq_msg_payload = memreq_msg;
    netreq_msg_payload.opaque[mo-1 -: ns] = src_id[ns-1:0];
  end

  // build the header for the network message
  // Destination depends on whether this is single bank
  // If multi-bank, use bits from the memory address as the dest id
  assign netreq_msg_hdr.dest   = p_single_bank ? {c_net_srcdest_nbits{1'b0}}
                                   : memreq_msg.addr[c_dest_addr_lsb +: c_net_srcdest_nbits];
  assign netreq_msg_hdr.src    = src_id;
  assign netreq_msg_hdr.opaque = {c_net_opaque_nbits{1'b0}};

  // The bits of the opaque field that were used for tracking the resp
  // destination need to be zeroed out
  always_comb begin
    memresp_msg = netresp_msg_payload;
    memresp_msg.opaque[mo-1 -: ns] = {ns{1'b0}};
  end

endmodule

module lab5_mcore_16BDownstreamAdapter
(
  input  logic [c_net_srcdest_nbits-1:0] src_id,

  output mem_req_16B_t                   memreq_msg,

  input  net_hdr_t                       netreq_msg_hdr,
  input  mem_req_16B_t                   netreq_msg_payload,

  input  mem_resp_16B_t                  memresp_msg,

  output net_hdr_t                       netresp_msg_hdr,
  output mem_resp_16B_t                  netresp_msg_payload
);

  // memory-related parameters
  localparam c_mem_opaque_nbits = 8;

  // network-related parameters
  localparam c_net_srcdest_nbits = 2;
  localparam c_net_opaque_nbits  = 8;

  // shorter names for memory parameters
  localparam mo = c_mem_opaque_nbits;

  // shorter names for network parameters
  localparam ns = c_net_srcdest_nbits;

  // The memory request is just the payload sent over the network
  assign memreq_msg = netreq_msg_payload;
 
  // Construct the network header, recover dest from the opaque bits
  assign netresp_msg_hdr.src    = src_id[ns-1:0];
  assign netresp_msg_hdr.dest   = memresp_msg.opaque[mo-1 -: ns];
  assign netresp_msg_hdr.opaque = {c_net_opaque_nbits{1'b0}};

  // Payload sent is unmodified from original message
  assign netresp_msg_payload = memresp_msg;

endmodule

module lab5_mcore_4BDownstreamAdapter
(
  input  logic [c_net_srcdest_nbits-1:0] src_id,

  output mem_req_4B_t                    memreq_msg,

  input  net_hdr_t                       netreq_msg_hdr,
  input  mem_req_4B_t                    netreq_msg_payload,

  input  mem_resp_4B_t                   memresp_msg,

  output net_hdr_t                       netresp_msg_hdr,
  output mem_resp_4B_t                   netresp_msg_payload
);

  // memory-related parameters
  localparam c_mem_opaque_nbits = 8;

  // network-related parameters
  localparam c_net_srcdest_nbits = 2;
  localparam c_net_opaque_nbits  = 8;

  // shorter names for memory parameters
  localparam mo = c_mem_opaque_nbits;

  // shorter names for network parameters
  localparam ns = c_net_srcdest_nbits;

  // The memory request is just the payload sent over the network
  assign memreq_msg = netreq_msg_payload;
 
  // Construct the network header, recover dest from the opaque bits
  assign netresp_msg_hdr.src    = src_id[ns-1:0];
  assign netresp_msg_hdr.dest   = memresp_msg.opaque[mo-1 -: ns];
  assign netresp_msg_hdr.opaque = {c_net_opaque_nbits{1'b0}};

  // Payload sent is unmodified from original message
  assign netresp_msg_payload = memresp_msg;

endmodule

`endif /* LAB5_MCORE_MEM_NET_MSG_ADAPTERS_V */
