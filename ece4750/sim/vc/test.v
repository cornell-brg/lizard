//========================================================================
// Macros for unit tests
//========================================================================
// This file contains various macros to help write unit tests for
// small verilog blocks. Here is a simple example of a test harness
// for a two input mux.
//
// `include "vc-test.v"
//
// module tester;
//
//  logic clk = 1'b1;
//  always #5 clk = ~clk;
//
//  `VC_TEST_SUITE_BEGIN( "vc_Muxes" );
//
//  logic [31:0] mux2_in0;
//  logic [31:0] mux2_in0;
//  logic        mux2_sel;
//  logic [31:0] mux2_out;
//
//  vc_Mux2#(32) mux2( mux2_in0, mux2_in1, mux2_sel, mux2_out );
//
//  `VC_TEST_CASE_BEGIN( 1, "vc_Mux2" )
//  begin
//
//    mux2_in0 = 32'h0a0a0a0a;
//    mux2_in1 = 32'hb0b0b0b0;
//
//    mux2_sel = 1'd0;
//    #25;
//    `VC_TEST_NET( mux2_out, 32'h0a0a0a0a );
//
//    mux2_sel = 1'd1;
//    #25;
//    `VC_TEST_NET( mux2_out, 32'hb0b0b0b0 );
//
//  end
//  `VC_TEST_CASE_END
//
//  `VC_TEST_SUITE_END
// endmodule
//
// Note that you need a clk even if you are only testing a combinational
// block since the test infrastructure includes a clocked state element.
// Each of the macros are discussed in more detail below.
//
// By default only checks which fail are displayed. The user can specify
// verbose output using the +verbose=2 command line parameter. When
// verbose output is enabled, all checks are displayed regardless of
// whether or not they pass or fail.

`ifndef VC_TEST_V
`define VC_TEST_V

// We encapsulate the internal test variables in a module so that we
// don't clutter up the namespace. This should make looking a signals
// easier in the waveform viewer.

module vc_Test();
  integer cases_done = 1;
  integer verbose;
  integer case_num_only;
  integer case_num = 0;
  integer next_case_num = 0;
  integer num_cycles_cases_done = 0;
endmodule

//------------------------------------------------------------------------
// VC_TEST_SUITE_BEGIN( suite-name )
//------------------------------------------------------------------------
// The single parameter should be a quoted string indicating the name of
// the test suite.

`define VC_TEST_SUITE_BEGIN( name_ )                                    \
  vc_Test    vc_test();                                                 \
                                                                        \
  logic        clk = 1'b1;                                              \
                                                                        \
  initial begin                                                         \
    if ( !$value$plusargs( "test-case=%d", vc_test.case_num_only ) ) begin \
      vc_test.case_num_only = 0;                                        \
    end                                                                 \
    if ( !$value$plusargs( "verbose=%d", vc_test.verbose ) ) begin      \
      vc_test.verbose = 0;                                              \
    end                                                                 \
    if ( $test$plusargs( "help" ) ) begin                               \
      $display( "" );                                                   \
      $display( " %s [options]",{name_,"-test"} );                      \
      $display( "" );                                                   \
      $display( "   +help               : this message" );              \
      $display( "   +test-case=<int>    : execute just given test case" ); \
      $display( "   +trace=<int>        : enable line tracing" ); \
      $display( "   +verbose=<int>      : enable more verbose output" ); \
      $display( "" );                                                   \
      $finish;                                                          \
    end                                                                 \
    if ( $test$plusargs( "dump-vcd" ) ) begin                           \
      $dumpfile({name_,"-test.vcd"});                                   \
      $dumpvars;                                                        \
    end                                                                 \
    $display("");                                                       \
    $display(" Test Suite: %s", name_ );                                \
  end                                                                   \
                                                                        \
  always #5 clk = ~clk;                                                 \
                                                                        \
  always_comb                                                           \
    if ( vc_test.case_num == 0 )                                        \
    begin                                                               \
      #20;                                                              \
      if ( vc_test.case_num_only != 0 )                                 \
        vc_test.next_case_num = vc_test.case_num_only;                  \
      else                                                              \
        vc_test.next_case_num = vc_test.case_num + 1;                   \
    end                                                                 \
                                                                        \
  always_ff @( posedge clk )                                            \
    vc_test.case_num <= vc_test.next_case_num;

//------------------------------------------------------------------------
// VC_TEST_SUITE_END
//------------------------------------------------------------------------
// You must include this macro at the end of the tester module right
// before endmodule.

`define VC_TEST_SUITE_END                                               \
  always_ff @( posedge clk ) begin                                      \
                                                                        \
    if ( vc_test.num_cycles_cases_done > 3 ) begin                      \
      $display("");                                                     \
      $finish;                                                          \
    end                                                                 \
                                                                        \
    if ( vc_test.cases_done )                                           \
      vc_test.num_cycles_cases_done <= vc_test.num_cycles_cases_done + 1; \
    else                                                                \
      vc_test.num_cycles_cases_done <= 0;                               \
                                                                        \
  end

//------------------------------------------------------------------------
// VC_TEST_CASE_BEGIN( test-case-num, test-case-name )
//------------------------------------------------------------------------
// This should directly proceed a begin-end block which contains the
// actual test case code. The test-case-num must be an increasing
// number and it must be unique. It is very easy to accidently reuse a
// test case number and this will cause multiple test cases to run
// concurrently jumbling the corresponding output.

// NOTE: Ackerley Tng changed this from always @(*) to explicitly denote
// the four signals the test case should trigger off of. This fixed some
// subtle bug he was seeing, and he included this comment in his code:
//
// "Note the use of a very specific always block sensitivity list here.
// We want to be very specific (instead of using always @ (*)) so that we
// don't want vc_test.cases_done or any other variable to change by
// accident just because a signal mentioned in the code between the two
// macros (where the macros are used) changes."
//
// Not sure I absolutely understand this, but it seems to make sense. We
// really only want the test case to fire when the case number
// increments. -cbatten

`define VC_TEST_CASE_BEGIN( num_, name_ )                               \
  always @( vc_test.case_num or vc_test.cases_done or                   \
            vc_test.verbose or vc_test.case_num_only ) begin            \
    if ( vc_test.case_num == num_ ) begin                               \
      if ( vc_test.cases_done == 0 ) begin                              \
        $display( "\n FAILED: Test case %s has the same test case number (%x) as another test case!\n", name_, num_ ); \
        $finish;                                                        \
      end                                                               \
      vc_test.cases_done = 0;                                           \
      $display( "  + Test Case %0d: %s", num_, name_ );

//------------------------------------------------------------------------
// VC_TEST_CASE_END
//------------------------------------------------------------------------
// This should directly follow the begin-end block for the test case.

`define VC_TEST_CASE_END                                                \
      vc_test.cases_done = 1;                                           \
      if ( vc_test.case_num_only != 0 )                                 \
        vc_test.next_case_num = 1023;                                   \
      else                                                              \
        vc_test.next_case_num = vc_test.case_num + 1;                   \
    end                                                                 \
  end

//------------------------------------------------------------------------
// VC_TEST_NOTE( msg )
//------------------------------------------------------------------------
// Output some text only if verbose

`define VC_TEST_NOTE( msg_ )                                            \
  if ( vc_test.verbose > 2 )                                            \
    $display( "                %s", msg_ );                             \
  if (1)

//------------------------------------------------------------------------
// VC_TEST_NOTE_INPUTS_1( in1_ )
//------------------------------------------------------------------------

`define VC_TEST_NOTE_INPUTS_1( in1_ )                                   \
  if ( vc_test.verbose > 0 )                                            \
    $display( "                Inputs:%s", "in1_ = ", in1_ );           \
  if (1)

//------------------------------------------------------------------------
// VC_TEST_NOTE_INPUTS_2( in1_, in2_ )
//------------------------------------------------------------------------

`define VC_TEST_NOTE_INPUTS_2( in1_, in2_ )                             \
  if ( vc_test.verbose > 0 )                                            \
    $display( "                Inputs:%s = %x,%s = %x",                 \
              "in1_", in1_, "in2_", in2_ );                             \
  if (1)

//------------------------------------------------------------------------
// VC_TEST_NOTE_INPUTS_3( in1_, in2_, in3_ )
//------------------------------------------------------------------------

`define VC_TEST_NOTE_INPUTS_3( in1_, in2_, in3_ )                       \
  if ( vc_test.verbose > 0 )                                            \
    $display( "                Inputs:%s = %x,%s = %x,%s = %x",         \
              "in1_", in1_, "in2_", in2_, "in3_", in3_ );               \
  if (1)

//------------------------------------------------------------------------
// VC_TEST_NOTE_INPUTS_4( in1_, in2_, in3_, in4_ )
//------------------------------------------------------------------------

`define VC_TEST_NOTE_INPUTS_4( in1_, in2_, in3_, in4_ )                 \
  if ( vc_test.verbose > 0 )                                            \
    $display( "                Inputs:%s = %x,%s = %x,%s = %x,%s = %x", \
              "in1_", in1_, "in2_", in2_, "in3_", in3_, "in4_", in4_ ); \
  if (1)

//------------------------------------------------------------------------
// VC_TEST_NET( tval_, cval_ )
//------------------------------------------------------------------------
// This macro is used to check that tval == cval.

`define VC_TEST_NET( tval_, cval_ )                                     \
  if ( tval_ === 'hz ) begin                                            \
    $display( "     [ FAILED ]%s, expected = %x, actual = %x",          \
              "tval_", cval_, tval_ );                                  \
  end                                                                   \
  else                                                                  \
  casez ( tval_ )                                                       \
    cval_ :                                                             \
      if ( vc_test.verbose > 0 )                                        \
         $display( "     [ passed ]%s, expected = %x, actual = %x",     \
                   "tval_", cval_, tval_ );                             \
    default : begin                                                     \
      $display( "     [ FAILED ]%s, expected = %x, actual = %x",        \
                "tval_", cval_, tval_ );                                \
    end                                                                 \
  endcase                                                               \
  if (1)

//------------------------------------------------------------------------
// VC_TEST_FAIL( tval_, msg_ )
//------------------------------------------------------------------------
// This macro is used to force a failure and display some message. This is
// useful if we want to fail due to some reason other than equality.

`define VC_TEST_FAIL( tval_, msg_ )                                     \
  $display( "     [ FAILED ]%s, actual = %x, %s",                       \
            "tval_", tval_, msg_ );                                     \
  if (1)

`endif /* VC_TEST_V */

