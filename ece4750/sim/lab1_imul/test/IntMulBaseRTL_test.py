#=========================================================================
# IntMulBaseRTL_test
#=========================================================================

import pytest

from pymtl         import *
from pclib.test    import run_sim

from lab1_imul.IntMulBaseRTL import IntMulBaseRTL

#-------------------------------------------------------------------------
# Reuse tests from FL model
#-------------------------------------------------------------------------

from IntMulFL_test import TestHarness, test_case_table

@pytest.mark.parametrize( **test_case_table )
def test( test_params, dump_vcd, test_verilog ):
  run_sim( TestHarness( IntMulBaseRTL(),
                        test_params.msgs[::2], test_params.msgs[1::2],
                        test_params.src_delay, test_params.sink_delay,
                        dump_vcd, test_verilog ), dump_vcd, max_cycles=20000 )

