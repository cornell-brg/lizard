//=========================================================================
// Alternative Blocking Cache Datapath
//=========================================================================

`ifndef LAB3_MEM_BLOCKING_CACHE_ALT_DPATH_V
`define LAB3_MEM_BLOCKING_CACHE_ALT_DPATH_V

`include "vc/mem-msgs.v"
`include "vc/regs.v"
`include "vc/muxes.v"
`include "vc/srams.v"
`include "vc/arithmetic.v"


`include "lab3_mem/BlockingCacheMagicNumbersAlt.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab3_mem_BlockingCacheAltDpathVRTL
#(
  parameter p_idx_shamt    = 0
)
(
  input  logic                        clk,
  input  logic                        reset,

  // Cache Request

  input  mem_req_4B_t                 cachereq_msg,

  // Cache Response

  output mem_resp_4B_t                cacheresp_msg,

  // Memory Request

  output mem_req_16B_t                memreq_msg,

  // Memory Response

  input  mem_resp_16B_t               memresp_msg,

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Add dpath signals
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  input logic                       cachereq_en,
  input logic                       write_data_mux_sel,
  output logic [2:0]                cachereq_type,
  output logic [31:0]               cachereq_addr,
  input logic                       tag_array_ren,
  input logic                       tag_array_wen,
  input logic                       memreq_addr_mux_sel,
  input logic                       data_array_ren,
  input logic                       data_array_wen,
  input logic [15:0]                data_array_wben,
  input logic [2:0]                 read_word_mux_sel,
  output logic                      tag_match_way0,
  output logic                      tag_match_way1,
  input logic [1:0]                 hit,
  input logic [2:0]                 cacheresp_type,
  input logic [2:0]                 memreq_type,
  input logic                       which_way
);

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Implement data-path
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

// Opaque reg
logic [(o-1):0] cachereq_opaque_reg_out;
vc_EnResetReg #(.p_nbits(o)) cachereq_opaque_reg
(
  .clk(clk),   // Clock input
  .reset(reset), // Sync reset input
  .q(cachereq_opaque_reg_out),     // Data output
  .d(cachereq_msg.opaque),      // Data input
  .en(cachereq_en)
);

// Request type reg
vc_EnResetReg #(.p_nbits(3)) cachereq_type_reg
(
  .clk(clk),   // Clock input
  .reset(reset), // Sync reset input
  .q(cachereq_type),     // Data output
  .d(cachereq_msg.type_),      // Data input
  .en(cachereq_en)
);

// Address reg
vc_EnResetReg #(.p_nbits(abw)) cachereq_addr_reg
(
  .clk(clk),   // Clock input
  .reset(reset), // Sync reset input
  .q(cachereq_addr),     // Data output
  .d(cachereq_msg.addr),      // Data input
  .en(cachereq_en)
);

// Request data reg
logic [(abw-1):0] cachereq_data_out;
vc_EnResetReg #(.p_nbits(abw)) cachereq_data_reg
(
  .clk(clk),   // Clock input
  .reset(reset), // Sync reset input
  .q(cachereq_data_out),     // Data output
  .d(cachereq_msg.data),      // Data input
  .en(cachereq_en)
);

logic [(clw-1):0] cachereq_data_repl;

// repl
assign cachereq_data_repl =
    {cachereq_data_out, cachereq_data_out, cachereq_data_out, cachereq_data_out};

// memresp
logic [(clw-1):0] memresp_data_out;
assign memresp_data_out = memresp_msg.data;



logic [(clw-1):0] write_data;

vc_Mux2 #(.p_nbits(clw)) write_data_mux
(
  .in0(memresp_data_out), //from memresp_data_reg
  .in1(cachereq_data_repl), //from repl
  .sel(write_data_mux_sel),
  .out(write_data)
);


logic [(idw-1):0] cachereq_addr_idx;
logic [(tgw-1):0] cachereq_addr_tag;
 //extract the idx depnding on the weird p_idx_shamt parameter
assign cachereq_addr_idx = cachereq_addr[ofw+(idw-1)+p_idx_shamt:ofw+p_idx_shamt];
assign cachereq_addr_tag = cachereq_addr[(abw-1):ofw]; //extract the "tag"


logic [(tgw-1):0] tag_array_read_data_way0;
logic [(tgw-1):0] tag_array_read_data_way1;

// The tag arary way0
vc_CombinationalBitSRAM_1rw
#(
  .p_data_nbits(tgw), //tag is 24 bits + 4 for the index
  .p_num_entries(nby) //16 cache lines
)
tag_array_way0
(
  .clk(clk),
  .reset(reset),

  // Read port (combinational read)
  .read_en(tag_array_ren),
  .read_addr(cachereq_addr_idx),
  .read_data(tag_array_read_data_way0),

  // Write port (sampled on the rising clock edge)
  .write_en(tag_array_wen && which_way==1'b0),
  .write_addr(cachereq_addr_idx),
  .write_data(cachereq_addr_tag)
);

// The tag arary way1
vc_CombinationalBitSRAM_1rw
#(
  .p_data_nbits(tgw), //tag is 24 bits + 4 for the index
  .p_num_entries(nby) //16 cache lines
)
tag_array_way1
(
  .clk(clk),
  .reset(reset),

  // Read port (combinational read)
  .read_en(tag_array_ren),
  .read_addr(cachereq_addr_idx),
  .read_data(tag_array_read_data_way1),

  // Write port (sampled on the rising clock edge)
  .write_en(tag_array_wen && which_way==1'b1),
  .write_addr(cachereq_addr_idx),
  .write_data(cachereq_addr_tag)
);

logic [(tgw-1):0] tag_array_read_data_out;
// Tag array data out
vc_Mux2 #(.p_nbits(tgw)) tag_addr_mux
(
  .in0(tag_array_read_data_way0),
  .in1(tag_array_read_data_way1),
  .sel(which_way),
  .out(tag_array_read_data_out)
);

// cmp block to see if tag match way0
vc_EqComparator #(.p_nbits(tgw)) cmp_way0
(
  .in0(cachereq_addr_tag),
  .in1(tag_array_read_data_way0),
  .out(tag_match_way0)
);

// cmp block to see if tag match way1
vc_EqComparator #(.p_nbits(tgw)) cmp_way1
(
  .in0(cachereq_addr_tag),
  .in1(tag_array_read_data_way1),
  .out(tag_match_way1)
);

logic [(abw-1):0] read_data_mkaddr_out;
assign read_data_mkaddr_out = { tag_array_read_data_out, {ofw{1'b0}} } ;


logic [(abw-1):0] cachereq_addr_tag_mkaddr_out;
assign cachereq_addr_tag_mkaddr_out = {cachereq_addr_tag, {ofw{1'b0}} };


logic [(abw-1):0] memreq_addr_mux_out;
// The memreq_addr_mux
vc_Mux2 #(.p_nbits(abw)) memreq_addr_mux
(
  .in0(cachereq_addr_tag_mkaddr_out),
  .in1(read_data_mkaddr_out),
  .sel(memreq_addr_mux_sel),
  .out(memreq_addr_mux_out)
);


logic [(clw-1):0] data_array_read_data_way0;
logic [(clw-1):0] data_array_read_data_way1;

// The data array way0
vc_CombinationalSRAM_1rw
#(
  .p_data_nbits(clw), // 128-bit entries, 4 words
  .p_num_entries(nby) //16 cache lines
)
data_array_way0
(
  .clk(clk),
  .reset(reset),

  // Read port (combinational read)
  .read_en(data_array_ren),
  .read_addr(cachereq_addr_idx),
  .read_data(data_array_read_data_way0),

  // Write port (sampled on the rising clock edge)
  .write_en(data_array_wen && which_way==1'b0),
  .write_byte_en(data_array_wben),
  .write_addr(cachereq_addr_idx),
  .write_data(write_data)
);

// The data array way1
vc_CombinationalSRAM_1rw
#(
  .p_data_nbits(clw), // 128-bit entries, 4 words
  .p_num_entries(nby) //16 cache lines
)
data_array_way1
(
  .clk(clk),
  .reset(reset),

  // Read port (combinational read)
  .read_en(data_array_ren),
  .read_addr(cachereq_addr_idx),
  .read_data(data_array_read_data_way1),

  // Write port (sampled on the rising clock edge)
  .write_en(data_array_wen && which_way==1'b1),
  .write_byte_en(data_array_wben),
  .write_addr(cachereq_addr_idx),
  .write_data(write_data)
);

logic [(clw-1):0] read_data_mux_out;

// We need a mux to choose which data output
vc_Mux2 #(.p_nbits(clw)) data_array_mux
(
  .in0(data_array_read_data_way0),
  .in1(data_array_read_data_way1),
  .sel(which_way),
  .out(read_data_mux_out)
);



logic [(dbw-1):0] read_word_mux_out;
// extract correct 32 bit word from output of data
vc_Mux5 #(.p_nbits(dbw)) read_word_mux
(
  .in0(0),
  .in1(read_data_mux_out[(dbw-1):0]),
  .in2(read_data_mux_out[(2*dbw-1):dbw]),
  .in3(read_data_mux_out[(3*dbw-1):(2*dbw)]),
  .in4(read_data_mux_out[(4*dbw-1):(3*dbw)]),
  .sel(read_word_mux_sel),
  .out(read_word_mux_out)
);

//cacheresp_msg
assign cacheresp_msg.opaque = cachereq_opaque_reg_out;
assign cacheresp_msg.type_ = cacheresp_type;
assign cacheresp_msg.len = 2'b0;
assign cacheresp_msg.test = hit;
assign cacheresp_msg.data = read_word_mux_out;

//memreq_msg
assign memreq_msg.type_ = memreq_type;
assign memreq_msg.len = 4'b0;
assign memreq_msg.addr = memreq_addr_mux_out;
assign memreq_msg.data = read_data_mux_out;
assign memreq_msg.opaque = {o{1'b0}};

endmodule

`endif
