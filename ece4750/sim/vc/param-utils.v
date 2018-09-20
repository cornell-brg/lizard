//========================================================================
// param-utils: parameterization utilities
//========================================================================


//------------------------------------------------------------------------
// Port pick: enables to have parameterized ports
//------------------------------------------------------------------------

`define VC_PORT_PICK_NBITS(nbits_,nports_) nbits_ * nports_

`define VC_PORT_PICK_MSB(nbits_,i_)                                     \
  ( i_ + 1 ) * nbits_ - 1

`define VC_PORT_PICK_FIELD(nbits_,i_)                                   \
  `VC_PORT_PICK_MSB(nbits_,i_) -: nbits_

//------------------------------------------------------------------------
// Generate call: allows programmatically index and call a generate block
//------------------------------------------------------------------------

// gen_its_: the number of iterations of generate block
// label_: the label the gen block is defined under
// i_    : the index we want to reach
// op_   : the operation to call (e.g. task call)
`define VC_GEN_CALL_2(label_,i_,op_)                                    \
  case( i_ )                                                            \
    0:  label_[0 ].op_;                                                 \
    1:  label_[1 ].op_;                                                 \
    default:                                                            \
    begin                                                               \
      $display( "Out of bounds: label_[i_]" );                          \
      $finish;                                                          \
    end                                                                 \
  endcase                                                               \
  if (1)

`define VC_GEN_CALL_4(label_,i_,op_)                                    \
  case( i_ )                                                            \
    0:  label_[0 ].op_;                                                 \
    1:  label_[1 ].op_;                                                 \
    2:  label_[2 ].op_;                                                 \
    3:  label_[3 ].op_;                                                 \
    default:                                                            \
    begin                                                               \
      $display( "Out of bounds: label_[i_]" );                          \
      $finish;                                                          \
    end                                                                 \
  endcase                                                               \
  if (1)

`define VC_GEN_CALL_8(label_,i_,op_)                                    \
  case( i_ )                                                            \
    0:  label_[0 ].op_;                                                 \
    1:  label_[1 ].op_;                                                 \
    2:  label_[2 ].op_;                                                 \
    3:  label_[3 ].op_;                                                 \
    4:  label_[4 ].op_;                                                 \
    5:  label_[5 ].op_;                                                 \
    6:  label_[6 ].op_;                                                 \
    7:  label_[7 ].op_;                                                 \
    default:                                                            \
    begin                                                               \
      $display( "Out of bounds: label_[i_]" );                          \
      $finish;                                                          \
    end                                                                 \
  endcase                                                               \
  if (1)


`define VC_GEN_CALL_16(label_,i_,op_)                                   \
  case( i_ )                                                            \
    0:  label_[0 ].op_;                                                 \
    1:  label_[1 ].op_;                                                 \
    2:  label_[2 ].op_;                                                 \
    3:  label_[3 ].op_;                                                 \
    4:  label_[4 ].op_;                                                 \
    5:  label_[5 ].op_;                                                 \
    6:  label_[6 ].op_;                                                 \
    7:  label_[7 ].op_;                                                 \
    8:  label_[8 ].op_;                                                 \
    9:  label_[9 ].op_;                                                 \
    10: label_[10].op_;                                                 \
    11: label_[11].op_;                                                 \
    12: label_[12].op_;                                                 \
    13: label_[13].op_;                                                 \
    14: label_[14].op_;                                                 \
    15: label_[15].op_;                                                 \
    default:                                                            \
    begin                                                               \
      $display( "Out of bounds: label_[i_]" );                          \
      $finish;                                                          \
    end                                                                 \
  endcase                                                               \
  if (1)

