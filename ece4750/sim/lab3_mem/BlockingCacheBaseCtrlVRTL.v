//=========================================================================
// Baseline Blocking Cache Control
//=========================================================================

`ifndef LAB3_MEM_BLOCKING_CACHE_BASE_CTRL_V
`define LAB3_MEM_BLOCKING_CACHE_BASE_CTRL_V

`include "vc/mem-msgs.v"
`include "vc/assert.v"
`include "vc/regfiles.v"

`include "lab3_mem/BlockingCacheMagicNumbersBase.v"


//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''<<<<<<< HEAD''''''''''''''''''

module lab3_mem_BlockingCacheBaseCtrlVRTL
#(
  parameter p_idx_shamt    = 0
)
(
  input  logic                        clk,
  input  logic                        reset,

  // Cache Request

  input  logic                        cachereq_val,
  output logic                        cachereq_rdy,

  // Cache Response

  output logic                        cacheresp_val,
  input  logic                        cacheresp_rdy,

  // Memory Request

  output logic                        memreq_val,
  input  logic                        memreq_rdy,

  // Memory Response

  input  logic                        memresp_val,
  output logic                        memresp_rdy,

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Define additional ports
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  output logic                       cachereq_en,
  output logic                       memresp_en,
  output logic                       write_data_mux_sel,
  input logic [2:0]                  cachereq_type,
  input logic [31:0]                 cachereq_addr,
  output logic                       tag_array_ren,
  output logic                       tag_array_wen,
  output logic                       data_array_ren,
  output logic                       data_array_wen,
  output logic [15:0]                data_array_wben,
  output logic                       read_data_reg_en,
  output logic [2:0]                 read_word_mux_sel,
  input logic                        tag_match,
  output logic                       evict_addr_reg_en,
  output logic                       memreq_addr_mux_sel,
  output logic [1:0]                 hit,
  output logic [2:0]                 cacheresp_type,
  output logic [2:0]                 memreq_type
  // YOU'RE WELCOME DREW FOR ROUTING ALL THESE IN FOR YOU
 );

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement control unit
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

// Used for reads
logic is_valid;
logic is_dirty;


// Used for writes
logic update_regfile;
logic set_valid;
logic set_dirty;

logic [1:0] rf_out;
logic [1:0] rf_in;

assign is_valid = rf_out[1:1];
assign is_dirty = rf_out[0:0];
assign rf_in = {set_valid, set_dirty};


assign cacheresp_type =
  (cachereq_type == `VC_MEM_REQ_MSG_TYPE_READ)  ? `VC_MEM_RESP_MSG_TYPE_READ :
  (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE) ? `VC_MEM_RESP_MSG_TYPE_WRITE :
  `VC_MEM_RESP_MSG_TYPE_WRITE_INIT;



logic [(ofw-2-1):0] cachereq_addr_offset;
logic [(idw-1):0] cachereq_addr_idx;

assign cachereq_addr_offset = cachereq_addr[(ofw-1):2];
assign cachereq_addr_idx = cachereq_addr[ofw+(idw-1)+p_idx_shamt:ofw+p_idx_shamt];


vc_Regfile_1r1w
#(
  .p_data_nbits(2), //valid and dirty bit
  .p_num_entries(nbl)
) val_dirty_regfile
(
  .clk(clk),
  .reset(reset),
  .read_addr(cachereq_addr_idx),
  .read_data(rf_out),
  .write_en(update_regfile),
  .write_addr(cachereq_addr_idx),
  .write_data(rf_in)
);

logic hit_in, hit_out, hit_en;

assign hit = {1'b0, hit_out};

vc_EnResetReg #(.p_nbits(1)) hit_reg
(
  .clk(clk),   // Clock input
  .reset(reset), // Sync reset input
  .q(hit_out),     // Data output
  .d(hit_in),      // Data input
  .en(hit_en)
);

  // FSM states
  typedef enum logic [3:0] {
      STATE_IDLE = 0,
      STATE_TAG_CHECK,
      STATE_INIT_DATA_ACCESS,
      STATE_READ_DATA_ACCESS,
      STATE_WAIT,
      STATE_WRITE_DATA_ACCESS,
      STATE_EVICT_PREPARE,
      STATE_REFILL_REQUEST,
      STATE_REFILL_UPDATE,
      STATE_EVICT_REQUEST,
      STATE_EVICT_WAIT,
      STATE_REFILL_WAIT
  } cache_state_t;


  cache_state_t state, next_state;

//figure out next state
always_comb begin
  case (state)
    STATE_IDLE: begin
      next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
    end

    STATE_TAG_CHECK: begin
      if (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE_INIT)
        next_state = STATE_INIT_DATA_ACCESS;
      else begin // not an init transaction
        if (!is_valid || (is_valid && !tag_match && !is_dirty)) begin //empty line or not dirty
          next_state = STATE_REFILL_REQUEST;
        end else if (is_valid && !tag_match && is_dirty ) begin // valid incorrect dirty line
          next_state = STATE_EVICT_PREPARE;
        end else begin //hit
          next_state = (cachereq_type == `VC_MEM_REQ_MSG_TYPE_READ) ?
                        STATE_READ_DATA_ACCESS : STATE_WRITE_DATA_ACCESS;
        end
      end
    end

    STATE_INIT_DATA_ACCESS: begin
      next_state = STATE_WAIT;
    end

    STATE_READ_DATA_ACCESS: begin
      next_state = STATE_WAIT;
    end

    STATE_WAIT: begin
      if (cacheresp_rdy)
          next_state = STATE_IDLE;
      else
          next_state = STATE_WAIT;
    end

    STATE_WRITE_DATA_ACCESS: begin
      next_state = STATE_WAIT;
    end

    STATE_EVICT_PREPARE: begin
      next_state = STATE_EVICT_REQUEST;
    end

    STATE_REFILL_REQUEST: begin
      next_state = (memreq_rdy) ? STATE_REFILL_WAIT : STATE_REFILL_REQUEST;
    end

    STATE_REFILL_WAIT: begin
      next_state = (memresp_val) ? STATE_REFILL_UPDATE : STATE_REFILL_WAIT;
    end

    STATE_REFILL_UPDATE: begin
      if (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE) begin
        next_state = STATE_WRITE_DATA_ACCESS;
      end else if (cachereq_type == `VC_MEM_REQ_MSG_TYPE_READ) begin
        next_state = STATE_READ_DATA_ACCESS;
      end else next_state = STATE_REFILL_UPDATE;
    end

    STATE_EVICT_REQUEST: begin
      next_state = memreq_rdy ? STATE_EVICT_WAIT : STATE_EVICT_REQUEST;
    end

    STATE_EVICT_WAIT: begin
      next_state = memresp_val ? STATE_REFILL_REQUEST : STATE_EVICT_WAIT;
    end

    default: begin

    end
  endcase
end //end always_ff



//assign next state
always_ff @(posedge clk) begin
  if (reset) begin
    state <= STATE_IDLE;
  end else begin
    state <= next_state;
  end //end else
end //end always_ff


task cs
(
  input cs_cachereq_en,
  input cs_memresp_en,
  input cs_write_data_mux_sel,
  input cs_tag_array_ren,
  input cs_tag_array_wen,
  input cs_data_array_ren,
  input cs_data_array_wen,
  input cs_read_data_reg_en,
  input cs_evict_addr_reg_en,
  input cs_memreq_addr_mux_sel,
  input cs_hit,
  input [2:0] cs_memreq_type,

  input cs_cachereq_rdy,
  input cs_cacheresp_val,
  input cs_memreq_val,
  input cs_memresp_rdy,
  input cs_update_regfile,
  input cs_set_valid,
  input cs_set_dirty
);
begin
  cachereq_en = cs_cachereq_en;
  memresp_en = cs_memresp_en;
  write_data_mux_sel = cs_write_data_mux_sel;
  tag_array_ren = cs_tag_array_ren;
  tag_array_wen = cs_tag_array_wen;
  data_array_ren = cs_data_array_ren;
  data_array_wen = cs_data_array_wen;
  read_data_reg_en = cs_read_data_reg_en;
  evict_addr_reg_en = cs_evict_addr_reg_en;
  memreq_addr_mux_sel = cs_memreq_addr_mux_sel;
  hit_en = cs_hit;
  memreq_type = cs_memreq_type;

  //module output signals
  cachereq_rdy = cs_cachereq_rdy; // Cache ready for new request
  cacheresp_val = cs_cacheresp_val; // Output valid
  memreq_val = cs_memreq_val; // outgoing memrequest
  memresp_rdy = cs_memresp_rdy; // accept incoming memresp
  update_regfile = cs_update_regfile;
  set_valid = cs_set_valid;
  set_dirty = cs_set_dirty;
end
endtask

assign read_word_mux_sel = cachereq_addr_offset+2'b1; //0 is 0, so need to add 1
assign hit_in = (tag_match && is_valid && (state != STATE_IDLE));

//figure out control signal outputs
always_comb begin
if (state == STATE_REFILL_UPDATE) begin
  data_array_wben = 16'hffff;
end else begin
  case (cachereq_addr_offset)
    // Only support word writes
    2'b00: data_array_wben = 16'h000f;
    2'b01: data_array_wben = 16'h00f0;
    2'b10: data_array_wben = 16'h0f00;
    2'b11: data_array_wben = 16'hf000;
    default: data_array_wben = 16'h0000;
  endcase
end



case (state)
  //                           cr    mr    wd    ta    ta    da    da    rd    ev    mr          mr    cr    cr   
  //                           en    en    mux   ren   wen   ren   wen   en    en   mux    hit   ty   rdy   val   mval  mrdy    wr    sv   sd
  STATE_IDLE:               cs( 1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    0,    1,    0,    0,    0,    0,    0,    0 );
  STATE_TAG_CHECK:          cs( 0,    0,    0,    1,    0,    1,    0,    1,    1,    0,    1,    0,    0,    0,    0,    0,    0,    0,    0 );
  STATE_INIT_DATA_ACCESS:   cs( 0,    0,    1,    0,    1,    0,    1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    1,    0 );
  STATE_READ_DATA_ACCESS:   cs( 0,    0,    0,    0,    0,    1,    0,    1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0 );
  STATE_WAIT:               cs( 0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    0,    0,    0,    0,    0 );
  STATE_WRITE_DATA_ACCESS:  cs( 0,    0,    1,    0,    1,    0,    1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    1,    1 );
  STATE_EVICT_PREPARE:      cs( 0,    0,    0,    1,    0,    0,    0,    0,    1,    0,    0,    0,    0,    0,    0,    0,    1,    0,    0 );
  STATE_EVICT_REQUEST:      cs( 0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    0,    1,    0,    0,    1,    0,    0,    0,    0 );
  STATE_EVICT_WAIT:         cs( 0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    0,    0,    0 );
  STATE_REFILL_REQUEST:     cs( 0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    0,    0,    0,    0 );
  STATE_REFILL_WAIT:        cs( 0,    1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0 );
  STATE_REFILL_UPDATE:      cs( 0,    0,    0,    0,    1,    0,    1,    0,    0,    0,    0,    0,    0,    0,    0,    1,    1,    1,    0 );
  default:                  cs( 1,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    1,    0,    0,    0,    0,    0,    0 );
endcase

end //end always_ff

endmodule

`endif
