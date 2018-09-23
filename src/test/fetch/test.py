import pytest
import random

from pymtl import *
from harness import *
from core.fetch.fl import FetchFL
from msg.fetch import FetchPacket
from config.general import RESET_VECTOR, ILEN


def test_simple():
    result = FetchPacket()
    result.pc = RESET_VECTOR
    result.instr = Bits(ILEN, 0xDEADBEEF)
    model = Harness(FetchFL, False, 0, 0, 0, 1, [result])
    model.elaborate()
    model.load_to_mem(RESET_VECTOR, result.instr)
    sim = SimulationTool(model)

    print()
    sim.reset()
    max_cycles = 10
    while not model.done() and sim.ncycles < max_cycles:
        sim.print_line_trace()
        sim.cycle()
    sim.print_line_trace()
    assert sim.ncycles < max_cycles
    model.cleanup()
