//========================================================================
// Verilog Components: Arbiters
//========================================================================
// There are three basic arbiter components which are provided in this
// file: vc_FixedArbChain, vc_VariableArbChain, vc_RoundRobinArbChain.
// These basic components can be combined in various ways to create the
// desired arbiter.

`ifndef VC_ARBITERS_V
`define VC_ARBITERS_V

`include "vc/regs.v"

//------------------------------------------------------------------------
// vc_FixedArbChain
//------------------------------------------------------------------------
// reqs[0] has the highest priority, reqs[1] has the second
// highest priority, etc.

module vc_FixedArbChain
#(
  parameter p_num_reqs = 2
)(
  input  logic                  kin,    // kill in
  input  logic [p_num_reqs-1:0] reqs,   // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants, // (one-hot) 1 indicates req won grant
  output logic                  kout    // kill out
);

  // The internal kills signals essentially form a kill chain from the
  // highest priority to the lowest priority requester. The highest
  // priority requster (say requester i) which is actually making a
  // request sets the kill signal for the next requester to one (ie
  // kills[i+1]) and then this kill signal is propagated to all lower
  // priority requesters.

  logic [p_num_reqs:0] kills;
  assign kills[0] = 1'b0;

  // The per requester logic first computes the grant signal and then
  // computes the kill signal for the next requester.

  logic [p_num_reqs-1:0] grants_int;

  genvar i;
  generate
  for ( i = 0; i < p_num_reqs; i = i + 1 )
  begin : per_req_logic

    // Grant is true if this requester is not killed and it is actually
    // making a req.

    assign grants_int[i] = !kills[i] && reqs[i];

    // Kill is true if this requester was either killed or it received
    // the grant.

    assign kills[i+1] = kills[i] || grants_int[i];

  end
  endgenerate

  // We AND kin into the grant and kout signals afterwards so that we can
  // begin doing the arbitration before we know kin. This also allows us
  // to build hybrid tree-ripple arbiters out of vc_FixedArbChain
  // components.

  assign grants = grants_int & {p_num_reqs{~kin}};
  assign kout   = kills[p_num_reqs] || kin;

endmodule

//------------------------------------------------------------------------
// vc_FixedArb
//------------------------------------------------------------------------
// reqs[0] has the highest priority, reqs[1] has the second highest
// priority, etc.

module vc_FixedArb
#(
  parameter p_num_reqs = 2
)(
  input  logic [p_num_reqs-1:0] reqs,  // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants // (one-hot) 1 = which req won grant
);

  logic dummy_kout;

  vc_FixedArbChain#(p_num_reqs) fixed_arb_chain
  (
    .kin    (1'b0),
    .reqs   (reqs),
    .grants (grants),
    .kout   (dummy_kout)
  );

endmodule

//------------------------------------------------------------------------
// vc_VariableArbChain
//------------------------------------------------------------------------
// The input priority signal is a one-hot signal where the one indicates
// which request should be given highest priority.

module vc_VariableArbChain
#(
  parameter p_num_reqs = 2
)(
  input  logic                  kin,       // kill in
  input  logic [p_num_reqs-1:0] priority_, // (one-hot) 1 is req w/ highest pri
  input  logic [p_num_reqs-1:0] reqs,      // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants,    // (one-hot) 1 is req won grant
  output logic                  kout       // kill out
);

  // The internal kills signals essentially form a kill chain from the
  // highest priority to the lowest priority requester. Unliked the fixed
  // arb, the priority input is used to determine which request has the
  // highest priority. We could use a circular kill chain, but static
  // timing analyzers would probably consider it a combinational loop
  // (which it is) and choke. Instead we replicate the kill chain. See
  // Principles and Practices of Interconnection Networks, Dally +
  // Towles, p354 for more info.

  logic [2*p_num_reqs:0] kills;
  assign kills[0] = 1'b1;

  logic [2*p_num_reqs-1:0] priority_int;
  assign priority_int = { {p_num_reqs{1'b0}}, priority_ };

  logic [2*p_num_reqs-1:0] reqs_int;
  assign reqs_int = { reqs, reqs };

  logic [2*p_num_reqs-1:0] grants_int;

  // The per requester logic first computes the grant signal and then
  // computes the kill signal for the next requester.

  localparam p_num_reqs_x2 = (p_num_reqs << 1);
  genvar i;
  generate
  for ( i = 0; i < 2*p_num_reqs; i = i + 1 )
  begin : per_req_logic

    // If this is the highest priority requester, then we ignore the
    // input kill signal, otherwise grant is true if this requester is
    // not killed and it is actually making a req.

    assign grants_int[i]
      = priority_int[i] ? reqs_int[i] : (!kills[i] && reqs_int[i]);

    // If this is the highest priority requester, then we ignore the
    // input kill signal, otherwise kill is true if this requester was
    // either killed or it received the grant.

    assign kills[i+1]
      = priority_int[i] ? grants_int[i] : (kills[i] || grants_int[i]);

  end
  endgenerate

  // To calculate final grants we OR the two grants from the replicated
  // kill chain. We also AND in the global kin signal.

  assign grants
    = (grants_int[p_num_reqs-1:0] | grants_int[2*p_num_reqs-1:p_num_reqs])
    & {p_num_reqs{~kin}};

  assign kout = kills[2*p_num_reqs] || kin;

endmodule

//------------------------------------------------------------------------
// vc_VariableArb
//------------------------------------------------------------------------
// The input priority signal is a one-hot signal where the one indicates
// which request should be given highest priority.

module vc_VariableArb
#(
  parameter p_num_reqs = 2
)(
  input  logic [p_num_reqs-1:0] priority_,  // (one-hot) 1 is req w/ highest pri
  input  logic [p_num_reqs-1:0] reqs,      // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants     // (one-hot) 1 is req won grant
);

  logic dummy_kout;

  vc_VariableArbChain#(p_num_reqs) variable_arb_chain
  (
    .kin       (1'b0),
    .priority_ (priority_),
    .reqs      (reqs),
    .grants    (grants),
    .kout      (dummy_kout)
  );

endmodule

//------------------------------------------------------------------------
// vc_RoundRobinArbChain
//------------------------------------------------------------------------
// Ensures strong fairness among the requesters. The requester which wins
// the grant will be the lowest priority requester the next cycle.

module vc_RoundRobinArbChain
#(
  parameter p_num_reqs             = 2,
  parameter p_priority_reset_value = 1  // (one-hot) 1 = high priority req
)(
  input  logic                  clk,
  input  logic                  reset,
  input  logic                  kin,    // kill in
  input  logic [p_num_reqs-1:0] reqs,   // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants, // (one-hot) 1 is req won grant
  output logic                  kout    // kill out
);

  // We only update the priority if a requester actually received a grant

  logic priority_en;
  assign priority_en = |grants;

  // Next priority is just the one-hot grant vector left rotated by one

  logic [p_num_reqs-1:0] priority_next;
  assign priority_next = { grants[p_num_reqs-2:0], grants[p_num_reqs-1] };

  // State for the one-hot priority vector

  logic [p_num_reqs-1:0] priority_;

  vc_EnResetReg#(p_num_reqs,p_priority_reset_value) priority_reg
  (
    .clk   (clk),
    .reset (reset),
    .en    (priority_en),
    .d     (priority_next),
    .q     (priority_)
  );

  // Variable arbiter chain

  vc_VariableArbChain#(p_num_reqs) variable_arb_chain
  (
    .kin       (kin),
    .priority_ (priority_),
    .reqs      (reqs),
    .grants    (grants),
    .kout      (kout)
  );

endmodule

//------------------------------------------------------------------------
// vc_RoundRobinArbEn
//------------------------------------------------------------------------
// Ensures strong fairness among the requesters. The requester which wins
// the grant will be the lowest priority requester the next cycle. Has an
// enable bit to control whether priorities should actually update.
//
//  NOTE : Ideally we would just instantiate the vc_RoundRobinArbChain
//         and wire up kin to zero, but VCS seems to have trouble with
//         correctly elaborating the parameteres in that situation. So
//         for now we just duplicate the code from vc_RoundRobinArbChain
//

module vc_RoundRobinArbEn #( parameter p_num_reqs = 2 )
(
  input  logic                clk,
  input  logic                reset,
  input  logic                en,        // 1 = update priorities
  input  logic [p_num_reqs-1:0] reqs,    // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants   // (one-hot) 1 is req won grant
);

  // We only update the priority if a requester actually received a grant

  logic priority_en;
  assign priority_en = |grants && en;

  // Next priority is just the one-hot grant vector left rotated by one

  logic [p_num_reqs-1:0] priority_next;
  assign priority_next = { grants[p_num_reqs-2:0], grants[p_num_reqs-1] };

  // State for the one-hot priority vector

  logic [p_num_reqs-1:0] priority_;

  vc_EnResetReg#(p_num_reqs,1) priority_reg
  (
    .clk   (clk),
    .reset (reset),
    .en    (priority_en),
    .d     (priority_next),
    .q     (priority_)
  );

  // Variable arbiter chain

  logic dummy_kout;

  vc_VariableArbChain#(p_num_reqs) variable_arb_chain
  (
    .kin       (1'b0),
    .priority_ (priority_),
    .reqs      (reqs),
    .grants    (grants),
    .kout      (dummy_kout)
  );

endmodule

//------------------------------------------------------------------------
// vc_RoundRobinArb
//------------------------------------------------------------------------
// Ensures strong fairness among the requesters. The requester which wins
// the grant will be the lowest priority requester the next cycle.
//
//  NOTE : Ideally we would just instantiate the vc_RoundRobinArbChain
//         and wire up kin to zero, but VCS seems to have trouble with
//         correctly elaborating the parameteres in that situation. So
//         for now we just duplicate the code from vc_RoundRobinArbChain
//

module vc_RoundRobinArb #( parameter p_num_reqs = 2 )
(
  input  logic                clk,
  input  logic                reset,
  input  logic [p_num_reqs-1:0] reqs,    // 1 = making a req, 0 = no req
  output logic [p_num_reqs-1:0] grants   // (one-hot) 1 is req won grant
);

  // We only update the priority if a requester actually received a grant

  logic priority_en;
  assign priority_en = |grants;

  // Next priority is just the one-hot grant vector left rotated by one

  logic [p_num_reqs-1:0] priority_next;
  assign priority_next = { grants[p_num_reqs-2:0], grants[p_num_reqs-1] };

  // State for the one-hot priority vector

  logic [p_num_reqs-1:0] priority_;

  vc_EnResetReg#(p_num_reqs,1) priority_reg
  (
    .clk   (clk),
    .reset (reset),
    .en    (priority_en),
    .d     (priority_next),
    .q     (priority_)
  );

  // Variable arbiter chain

  logic dummy_kout;

  vc_VariableArbChain#(p_num_reqs) variable_arb_chain
  (
    .kin       (1'b0),
    .priority_ (priority_),
    .reqs      (reqs),
    .grants    (grants),
    .kout      (dummy_kout)
  );

endmodule

`endif /* VC_ARBITERS_V */

