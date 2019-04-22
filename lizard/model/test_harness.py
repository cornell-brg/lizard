from pymtl import *
from lizard.util.rtl.interface import Interface, IncludeAll, UseInterface
from lizard.model.translate import translate


def TestHarness(target,
                dut,
                translate_model,
                vcd_file='',
                use_cached_verilated=False):
  test_harness_interface = Interface([], bases=[IncludeAll(dut.interface)])
  UseInterface(target, test_harness_interface)

  if translate_model:
    dut.vcd_file = vcd_file
    target.dut = translate(dut, use_cached_verilated=use_cached_verilated)
  else:
    target.dut = dut

  for name in target.interface.methods.keys():
    target.connect_m(getattr(target, name), getattr(target.dut, name))

  target.vcd_file = vcd_file
