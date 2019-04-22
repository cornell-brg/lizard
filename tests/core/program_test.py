#=========================================================================
# ProcAltRTL_branch_test.py
#=========================================================================

import pytest
import random
from program import collector

from pymtl import *
from tests.context import lizard
from tests.core.runner import run_test_elf
from lizard.core.rtl.proc_harness_rtl import mem_image_test
from lizard.util import elf

TEST_DIR = "program/"

opt_levels = range(4)
dir, tests = collector.collect()

collector.build_riscv_tests()
dir_bin, tests_bin = collector.collect_riscv_tests()


@pytest.mark.parametrize('opt_level', opt_levels)
@pytest.mark.parametrize('program', tests)
@pytest.mark.parametrize('translate', ['verilate', 'sim'])
def test_rtl_proc(program, opt_level, translate):
  # Build the program
  print("Building: %s" % program)
  outname = collector.build(program, opt_level)
  # Run it
  with open(outname, "rb") as fd:
    mem = elf.elf_reader(fd, True)
    name = translate + '-' + program + "-out.vcd"
    mem_image_test(mem, translate == 'verilate', name, max_cycles=200000)


@pytest.mark.parametrize('program', tests_bin)
@pytest.mark.parametrize('translate', ['verilate', 'sim'])
def test_riscv_rtl_proc(program, translate):
  outname = dir_bin + program
  # Run it
  with open(outname, "rb") as fd:
    mem = elf.elf_reader(fd, True)
    name = translate + '-' + program + "-out.vcd"
    mem_image_test(mem, translate == 'verilate', name, max_cycles=5000)
