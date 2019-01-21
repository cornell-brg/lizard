from pymtl import *
from util.test_utils import run_test_vector_sim
from util.rtl.snapshotting_freelist import SnapshottingFreeList
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      SnapshottingFreeList( 4, 1, 1, False, False, 4 ), [
          ( 'alloc_ports[0].call alloc_ports[0].rdy* alloc_ports[0].index* alloc_ports[0].mask* free_ports[0].call free_ports[0].index release_port.call set_port.call'
          ),
          ( 1, 1, 0, 0b0001, 0, 0, 0, 0 ),
          ( 1, 1, 1, 0b0010, 0, 0, 0, 0 ),
          ( 0, 1, '?', '?', 1, 0, 0, 0 ),
          ( 1, 1, 0, 0b0001, 0, 0, 0, 0 ),
          ( 1, 1, 2, 0b0100, 0, 0, 0, 0 ),
          ( 1, 1, 3, 0b1000, 0, 0, 0, 0 ),
          ( 0, 0, '?', '?', 1, 1, 0, 0 ),
          ( 1, 1, 1, 0b0010, 0, 0, 0, 0 ),
      ],
      dump_vcd="foobar.vcd",
      test_verilog=test_verilog )
