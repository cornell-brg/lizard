#=========================================================================
# ProcAltRTL_branch_test.py
#=========================================================================

import pytest
import random
from program import collector

from pymtl import *
from runner import run_test_elf
from proc_harness_cl import ProcTestHarnessCL
from proc_harness_fl import ProcTestHarnessFL

TEST_DIR = "program/"

procs = [ ProcTestHarnessFL, ProcTestHarnessCL ]
proc_dict = dict([( x.__name__, x ) for x in procs ] )
opt_levels = range( 4 )
dir, tests = collector.collect()


@pytest.mark.parametrize( 'opt_level', opt_levels )
@pytest.mark.parametrize( 'program', tests )
@pytest.mark.parametrize( 'proc_key', proc_dict.keys() )
def test( proc_key, program, opt_level ):
  # Build the program
  print( "Building: %s" % program )
  outname = collector.build( program, opt_level )
  # Run it
  run_test_elf( proc_dict[ proc_key ], outname, 10000 )