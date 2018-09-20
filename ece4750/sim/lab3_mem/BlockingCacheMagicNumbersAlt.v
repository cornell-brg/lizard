`ifndef LAB3_MEM_BLOCKING_CACHE_MAGIC_NUMBERS_ALT
`define LAB3_MEM_BLOCKING_CACHE_MAGIC_NUMBERS_ALT

// local parameters not meant to be set from outside
localparam size = 256;             // Cache size in bytes
localparam dbw  = 32;              // Short name for data bitwidth
localparam abw  = 32;              // Short name for addr bitwidth
localparam o    = 8;               // Short name for opaque bitwidth
localparam clw  = 128;             // Short name for cacheline bitwidth
localparam nbl  = size*8/clw;      // Number of blocks in the cache
localparam nby  = nbl/2;           // Number of blocks per way
localparam idw  = $clog2(nby);     // Short name for index bitwidth
localparam ofw  = $clog2(clw/8);   // Short name for the offset bitwidth
// In this lab, to simplify things, we always use all bits except for the
// offset in the tag, rather than storing the "normal" 24 bits. This way,
// when implementing a multi-banked cache, we don't need to worry about
// re-inserting the bank id into the address of a cacheline.
localparam tgw  = abw - ofw;       // Short name for the tag bitwidth


// FSM states
typedef enum logic [3:0] {
  STATE_IDLE = 0,
  STATE_TAG_CHECK,
  STATE_INIT_DATA,
  STATE_WAIT,
  STATE_WRITE_DATA,
  STATE_WRITE_DATA_RDY,
  STATE_REFILL,
  STATE_EVICT_WAIT,
  STATE_REFILL_WAIT,
  STATE_READ_DATA
} cache_state_t;

`endif
