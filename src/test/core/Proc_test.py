#=========================================================================
# ProcAltRTL_branch_test.py
#=========================================================================

import pytest
import random

from pymtl   import *
from harness import *
from core.fl import CoreFL
from inst_modules import inst_modules

procs = [CoreFL]
proc_dict = dict([(x.__name__, x) for x in procs])

def idfn(val):
  return val[0]

@pytest.mark.parametrize( 'rand_delays', ['rd', 'nd'] )
@pytest.mark.parametrize( 'name_and_func', extract_tests(inst_modules()), ids=idfn )
@pytest.mark.parametrize( 'proc_key', proc_dict.keys() )
def test( name_and_func, proc_key, rand_delays, dump_vcd=False ):
  test = name_and_func[1]
  proc = proc_dict[proc_key]
  if rand_delays == 'rd':
    if 'inst_btb' not in name_and_func[0]:
      run_test( proc, test, dump_vcd, src_delay=3, sink_delay=5, mem_stall_prob=0.5, mem_latency=3)
    else:
      pytest.skip("No delays on predictor stress tests.")
  else:
    run_test( proc, test, dump_vcd )
