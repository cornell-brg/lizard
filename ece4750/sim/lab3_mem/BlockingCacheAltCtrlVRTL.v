//=========================================================================
// Alternative Blocking Cache Control Unit
//=========================================================================

`ifndef LAB3_MEM_BLOCKING_CACHE_ALT_CTRL_V
`define LAB3_MEM_BLOCKING_CACHE_ALT_CTRL_V

`include "vc/mem-msgs.v"
`include "vc/assert.v"
`include "vc/regfiles.v"


`include "lab3_mem/BlockingCacheMagicNumbersAlt.v"

//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
// LAB TASK: Include necessary files
//''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

module lab3_mem_BlockingCacheAltCtrlVRTL
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
  // LAB TASK: Add control signals
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  output logic                       cachereq_en,
  output logic                       write_data_mux_sel,
  input logic [2:0]                  cachereq_type,
  input logic [31:0]                 cachereq_addr,
  output logic                       tag_array_ren,
  output logic                       tag_array_wen,
  output logic                       memreq_addr_mux_sel,
  output logic                       data_array_ren,
  output logic                       data_array_wen,
  output logic [15:0]                data_array_wben,
  output logic [2:0]                 read_word_mux_sel,
  input logic                        tag_match_way0,
  input logic                        tag_match_way1,
  output logic [1:0]                 hit,
  output logic [2:0]                 cacheresp_type,
  output logic [2:0]                 memreq_type,
  output logic                       which_way
  );

  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  // LAB TASK: Implement control unit
  //''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

  // Track our state and next state
  cache_state_t state, next_state;

  /* OUTPUTS FROM REGISTER FILES */
  logic [1:0] rf_in;
  logic [1:0] rf_out_way0;
  logic [1:0] rf_out_way1;
  logic is_valid_way0;
  logic is_dirty_way0;
  logic is_valid_way1;
  logic is_dirty_way1;
  logic lru;


  /* INPUTS TO REGISTER FILES */
  logic update_regfile;
  logic update_lru;
  logic set_valid;
  logic set_dirty;
  logic set_lru;

  //way 0
  assign is_valid_way0 = rf_out_way0[1:1];
  assign is_dirty_way0 = rf_out_way0[0:0];

  // way 1
  assign is_valid_way1 = rf_out_way1[1:1];
  assign is_dirty_way1 = rf_out_way1[0:0];

  assign rf_in = {set_valid, set_dirty };

  assign cacheresp_type =
    (cachereq_type == `VC_MEM_REQ_MSG_TYPE_READ)  ? `VC_MEM_RESP_MSG_TYPE_READ :
    (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE) ? `VC_MEM_RESP_MSG_TYPE_WRITE :
    `VC_MEM_RESP_MSG_TYPE_WRITE_INIT;


  logic [(ofw-2-1):0] cachereq_addr_offset;
  logic [(idw-1):0] cachereq_addr_idx;

  assign cachereq_addr_offset = cachereq_addr[(ofw-1):2];
  assign cachereq_addr_idx = cachereq_addr[ofw+(idw-1)+p_idx_shamt:ofw+p_idx_shamt];


  // Way 0
  vc_Regfile_1r1w
  #(
    .p_data_nbits(2), //valid and dirty
    .p_num_entries(nby)
  ) val_dirty_regfile_way0
  (
    .clk(clk),
    .reset(reset),
    .read_addr(cachereq_addr_idx),
    .read_data(rf_out_way0),
    .write_en(update_regfile && which_way==1'b0),
    .write_addr(cachereq_addr_idx),
    .write_data(rf_in)
  );

  // Way 1
  vc_Regfile_1r1w
  #(
    .p_data_nbits(2), //valid and dirty
    .p_num_entries(nby)
  ) val_dirty_regfile_way1
  (
    .clk(clk),
    .reset(reset),
    .read_addr(cachereq_addr_idx),
    .read_data(rf_out_way1),
    .write_en(update_regfile && which_way==1'b1),
    .write_addr(cachereq_addr_idx),
    .write_data(rf_in)
  );

  // LRU
  vc_Regfile_1r1w
  #(
    .p_data_nbits(1), //lru
    .p_num_entries(nby)
  ) lru_regfile
  (
    .clk(clk),
    .reset(reset),
    .read_addr(cachereq_addr_idx),
    .read_data(lru),
    .write_en(update_lru),
    .write_addr(cachereq_addr_idx),
    .write_data(set_lru)
  );

  logic which_way_saved, which_way_sel;
  // Request type reg
  vc_EnResetReg #(.p_nbits(1)) which_way_reg
  (
    .clk(clk),   // Clock input
    .reset(reset), // Sync reset input
    .q(which_way_saved),
    .d(which_way_sel),
    .en(state == STATE_TAG_CHECK)
  );

  // we have to bypass the reg in tag check
  assign which_way = (state == STATE_TAG_CHECK) ? which_way_sel : which_way_saved;

  logic hit_in, hit_out, is_hit;

  vc_EnResetReg #(.p_nbits(1)) hit_reg
  (
    .clk(clk),   // Clock input
    .reset(reset), // Sync reset input
    .q(hit_out),     // Data output
    .d(hit_in),      // Data input
    .en(state == STATE_TAG_CHECK)
  );

  // we have to bypass the reg in tag check
  assign is_hit = (state == STATE_TAG_CHECK) ? hit_in : hit_out;


  assign hit_in =
    (tag_match_way0 && is_valid_way0) || (tag_match_way1 && is_valid_way1);

  // We have to bypass the reg if in tag check
  assign hit = {1'b0, is_hit};


  logic should_refill;
  assign should_refill = !is_hit &&
    ((which_way == 1'b0 && (!is_valid_way0 || (is_valid_way0 && !tag_match_way0 && !is_dirty_way0))) ||
    (which_way == 1'b1 && (!is_valid_way1 || (is_valid_way1 && !tag_match_way1 && !is_dirty_way1))));


  logic should_evict;
  assign should_evict = !is_hit &&
    ((which_way == 1'b0 && (is_valid_way0 && !tag_match_way0 && is_dirty_way0)) || // both valid and dirty
    (which_way == 1'b1 && (is_valid_way1 && !tag_match_way1 && is_dirty_way1)));


  // Determine which way to use lru
  logic which_way_lru;
  always_comb begin
    if (!is_valid_way0) begin
      which_way_lru = 1'b0;
    end else if (!is_valid_way1) begin
      which_way_lru = 1'b1;
    end else if (lru == 1'b0) begin // 0 was used last
      which_way_lru = 1'b1;
    end else begin
      which_way_lru = 1'b0;
    end
  end


  logic which_hit;
  // Assigns to outgoing control signals
  // data mux selects which one hit, unless evict
  assign which_hit = (tag_match_way1 && is_valid_way1) ? 1'b1 : 1'b0;

  // This is the input to our which_way register
  assign which_way_sel = (hit_in) ? which_hit : which_way_lru;

  //figure out LRU update
  assign set_lru = which_way;

  logic mval_crdy;
  assign mval_crdy = memresp_val && (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE);

  logic write_hit;
  assign write_hit = hit_in && (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE);

  logic read_hit;
  assign read_hit = hit_in && (cachereq_type == `VC_MEM_REQ_MSG_TYPE_READ);

  // only case write is sent is in tag_check with evict
  assign memreq_type = ((state == STATE_TAG_CHECK) && should_evict) ?
        `VC_MEM_REQ_MSG_TYPE_WRITE : `VC_MEM_REQ_MSG_TYPE_READ;

  assign read_word_mux_sel = cachereq_addr_offset+2'b1; //0 is 0, so need to add 1



  //figure out control signal outputs
  always_comb begin
    if (state == STATE_REFILL_WAIT) begin
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
  end


  logic isdone; //is done

  //figure out next state
  always_comb begin
    isdone = 0;

    case (state)
      STATE_IDLE: begin
        isdone = 1;
        next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
      end

      STATE_TAG_CHECK: begin
        if (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE_INIT)
          next_state = STATE_INIT_DATA;
        else begin // not an init transaction
          if (should_refill) begin //empty line or not dirty
            next_state = (memreq_rdy) ? STATE_REFILL_WAIT : STATE_TAG_CHECK;
          end else if (should_evict) begin // valid incorrect dirty line
            next_state = (memreq_rdy) ? STATE_EVICT_WAIT : STATE_TAG_CHECK;
          end else if (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE) begin // write hit
            next_state = (cacheresp_rdy) ? STATE_WRITE_DATA_RDY : STATE_WRITE_DATA;
          end else begin // read hit
            if (cacheresp_rdy) begin
              isdone=1;
              next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
            end else begin
              next_state = STATE_WAIT;
            end
          end
        end
      end


      STATE_INIT_DATA: begin
        if (cacheresp_rdy) begin
            isdone = 1;
            next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
        end else begin
            next_state = STATE_WAIT;
        end
      end


      STATE_WAIT: begin
        if (cacheresp_rdy) begin
            isdone = 1;
            next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
        end else begin
            next_state = STATE_WAIT;
        end
      end


      STATE_WRITE_DATA: begin
        if (cacheresp_rdy) begin
          isdone = 1;
          next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
        end else begin
          next_state = STATE_WAIT;
        end
      end


      STATE_WRITE_DATA_RDY: begin
          isdone = 1;
          next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
      end


      STATE_EVICT_WAIT: begin
        if (memresp_val)
          next_state = STATE_REFILL;
        else
          next_state = STATE_EVICT_WAIT;
      end


      STATE_REFILL: begin
        next_state = (memreq_rdy) ? STATE_REFILL_WAIT : STATE_REFILL;
      end


      STATE_REFILL_WAIT: begin
        if  (!memresp_val)
          next_state = STATE_REFILL_WAIT;
        else if (cachereq_type == `VC_MEM_REQ_MSG_TYPE_WRITE)
          next_state = (cacheresp_rdy) ? STATE_WRITE_DATA_RDY : STATE_WRITE_DATA;
        else
          next_state = STATE_READ_DATA;
      end

      STATE_READ_DATA: begin
        if (cacheresp_rdy) begin
            isdone = 1;
            next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
        end else begin
            next_state = STATE_WAIT;
        end
      end


      default: begin
        next_state = cachereq_val ? STATE_TAG_CHECK : STATE_IDLE;
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
    input cs_write_data_mux_sel,
    input cs_memreq_addr_mux_sel,
    input cs_tag_array_ren,
    input cs_tag_array_wen,
    input cs_data_array_ren,
    input cs_data_array_wen,

    input cs_cacheresp_val,
    input cs_memreq_val,
    input cs_memresp_rdy,
    input cs_update_regfile,
    input cs_set_valid,
    input cs_set_dirty,
    input cs_update_lru
  );
  begin
    write_data_mux_sel = cs_write_data_mux_sel;
    memreq_addr_mux_sel = cs_memreq_addr_mux_sel;
    tag_array_ren = cs_tag_array_ren;
    tag_array_wen = cs_tag_array_wen;
    data_array_ren = cs_data_array_ren;
    data_array_wen= cs_data_array_wen;

    //module output signals
    cacheresp_val = cs_cacheresp_val; // Output valid
    memreq_val = cs_memreq_val; // outgoing memrequest
    memresp_rdy = cs_memresp_rdy; // accept incoming memresp
    update_regfile = cs_update_regfile;
    set_valid = cs_set_valid;
    set_dirty = cs_set_dirty;
    update_lru = cs_update_lru;
  end
  endtask

assign cachereq_en = isdone;
assign cachereq_rdy = isdone;

always_comb begin
  case (state)
  //                             wd    mr   ta    ta     da    da       cr                                  up
  //                             mux   mux  ren   wen   ren   wen       val   mval  mrdy    wr    sv   sd    lru
  STATE_IDLE:               cs(   0,    0,    0,    0,    0,    0,       0,    0,    0,    0,    0,    0,    0 );
  STATE_TAG_CHECK:          cs(1,should_evict,1,write_hit,1,write_hit, is_hit,!is_hit,1,   0,    0,    0,  read_hit );
  STATE_INIT_DATA:          cs(   1,    0,    0,    1,    0,    1,       1,    0,    0,    1,    1,    0,    1 );
  STATE_WRITE_DATA:         cs(   1,    0,    0,    1,    0,    1,       1,    0,    0,    1,    1,    1,    1 );
  STATE_WRITE_DATA_RDY:     cs(   1,    0,    0,    1,    0,    1,       0,    0,    0,    1,    1,    1,    1 );
  STATE_REFILL:             cs(   0,    0,    0,    0,    0,    0,       0,    1,    0,    0,    0,    0,    0 );
  STATE_REFILL_WAIT:        cs(   0,    0,    0,    1,    0,    1,   mval_crdy,0,    1,    1,    1,    0,    0 );
  STATE_EVICT_WAIT:         cs(   0,    0,    0,    0,    0,    0,       0,    0,    1,    0,    0,    0,    0 );
  STATE_READ_DATA:          cs(   0,    0,    0,    0,    1,    0,       1,    0,    0,    1,    1,    0,    1 );
  STATE_WAIT:               cs(   0,    0,    0,    0,    1,    0,       1,    0,    0,    0,    0,    0,    0 );
  default:                  cs(   0,    0,    0,    0,    0,    0,       0,    0,    0,    0,    0,    0,    0 );
  endcase
end //end always_ff

endmodule

`endif
