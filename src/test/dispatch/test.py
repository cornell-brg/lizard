import pytest
import random

from pymtl import *
from harness import *
from core.dispatch.fl import DispatchFL
from msg.decode import DecodePacket
from msg.fetch import FetchPacket
from msg.decode import *


def test_simple():
    source = FetchPacket()
    source.instr = 0b00000000000100001000000010010011  # AddI rs1, rs1, 1
    result = DecodePacket()
    result.imm = 1
    result.inst = RV64Inst.ADDI
    result.rs1 = 1
    result.rd = 1
    model = Harness(DispatchFL, [source], [result], 0)
    model.elaborate()
    sim = SimulationTool(model)

    sim.reset()
    max_cycles = 50
    while not model.done() and sim.ncycles < max_cycles:
        sim.print_line_trace()
        sim.cycle()
    sim.print_line_trace()
    assert sim.ncycles < max_cycles
