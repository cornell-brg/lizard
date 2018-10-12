import pytest
import random

from pymtl import *
from util.freelist import FreeList


def test_simple():
    model = FreeList(2)
    model.elaborate()
    sim = SimulationTool(model)

    print()
    sim.reset()
    max_cycles = 10
    while sim.ncycles < max_cycles:
        sim.print_line_trace()
        sim.cycle()
    sim.print_line_trace()
    assert sim.ncycles < max_cycles
    model.cleanup()
