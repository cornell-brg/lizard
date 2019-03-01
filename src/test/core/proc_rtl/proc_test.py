from test.core.proc_rtl.proc_harness_rtl import asm_test


def test_basic():
  asm_test(
      """
  addi x1, x0, 42
  nop
  nop
  nop
  nop
  nop
  nop
  csrw proc2mngr, x1 > 42
  """,
      True,
      'proc.vcd',
      max_cycles=200)
