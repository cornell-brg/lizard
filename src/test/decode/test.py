import pytest
import random

from pymtl import *
from harness import *
from core.cl.decode import DecodeUnitCL
from msg.decode import DecodePacket
from msg.fetch import FetchPacket
from msg.decode import *


@pytest.mark.skip( reason="needs CL test src/sink to test" )
def test_simple():
  source = FetchPacket()
  source.instr = 0b00000000000100001000000010010011  # AddI rs1, rs1, 1
  result = DecodePacket()
  result.imm = 1
  result.inst = RV64Inst.ADDI
  result.rs1 = 1
  result.rs1_valid = 1
  result.rd = 1
  result.rd_valid = 1
  model = Harness( DecodeUnitCL, [ source ], [ result ], 0 )
  model.elaborate()
  sim = SimulationTool( model )

  sim.reset()
  max_cycles = 50
  while not model.done() and sim.ncycles < max_cycles:
    sim.print_line_trace()
    sim.cycle()
  sim.print_line_trace()
  assert sim.ncycles < max_cycles
