#=========================================================================
# ProcAltRTL_branch_test.py
#=========================================================================

import pytest
import random

from pymtl import *
from runner import run_test, extract_tests
from proc_harness_cl import ProcTestHarnessCL
from proc_harness_fl import ProcTestHarnessFL
from inst_modules import inst_modules

procs = [ ProcTestHarnessFL, ProcTestHarnessCL ]
proc_dict = dict([( x.__name__, x ) for x in procs ] )


def idfn( val ):
  return val[ 0 ]


@pytest.mark.parametrize(
    'name_and_func', extract_tests( inst_modules() ), ids=idfn )
@pytest.mark.parametrize( 'proc_key', proc_dict.keys() )
def test( name_and_func, proc_key ):
  test = name_and_func[ 1 ]
  proc = proc_dict[ proc_key ]
  run_test( proc, test )
