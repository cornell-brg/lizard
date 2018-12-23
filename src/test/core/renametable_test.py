from pymtl import *
from util.test_utils import run_test_vector_sim, run_rdycall_test_vector_sim
from core.rtl.renametable import RenameTable
from test.config import test_verilog


def test_basic():
  run_test_vector_sim(
      RenameTable( 2, 4, 2, 1, 1, True, [ 0, 0 ] ),
      [
          ( 'read_ports[0].areg read_ports[0].preg* read_ports[1].areg read_ports[1].preg* write_ports[0].call write_ports[0].areg write_ports[0].preg snapshot_port.call snapshot_port.rdy* snapshot_port.id* restore_port.call restore_port.id free_snapshot_port.call free_snapshot_port.id'
          ),
          ( 0, 3, 1, 0, 1, 1, 1, 0, 1, '?', 0, 0, 0,
            0 ),  # read r0 and r1 as p0 and p1, write r1 as p1
          ( 0, 3, 1, 1, 0, 0, 0, 0, 1, '?', 0, 0, 0,
            0 ),  # read r0 and r1 as p3 and p1, no write
          ( 0, 3, 1, 1, 1, 1, 2, 1, 1, 0, 0, 0, 0,
            0 ),  # read r0 and r1 as p3 and p1, write r1 as p2, snapshot
          ( 0, 3, 1, 2, 1, 1, 0, 0, '?', 0, 0, 0, 0,
            0 ),  # read r0 and r1 as p3 and p2, write r1 as p0
          ( 0, 3, 1, 2, 0, 0, 0, 0, '?', 0, 1, 0, 0,
            0 ),  # read r0 and r1 as p3 and p2, restoring snapshot
      ],
      dump_vcd=None,
      test_verilog=test_verilog )


def test_basic_rdycall():
  run_rdycall_test_vector_sim(
      RenameTable( 2, 4, 2, 1, 1, True, [ 0, 0 ] ),
      [
          ( 'read_ports[0]         read_ports[1]         write_ports[0]         snapshot_port   restore_port   free_snapshot_port'
          ),
          ( 'arg(areg), ret(preg)  arg(areg), ret(preg)  arg(areg, preg), call  ret(id), call   arg(id), call  arg(id), call'
          ),
          (( 0, 3 ), ( 1, 0 ), ( 1, 1, 1 ), ( '?', 0 ), ( 0, 0 ),
           ( 0, 0 ) ),  # read r0 and r1 as p0 and p1, write r1 as p1
          (( 0, 3 ), ( 1, 1 ), ( 0, 0, 0 ), ( '?', 0 ), ( 0, 0 ),
           ( 0, 0 ) ),  # read r0 and r1 as p3 and p1, no write
          (( 0, 3 ), ( 1, 1 ), ( 1, 2, 1 ), ( 0, 1 ), ( 0, 0 ),
           ( 0, 0 ) ),  # read r0 and r1 as p3 and p1, write r1 as p2, snapshot
          (( 0, 3 ), ( 1, 2 ), ( 1, 0, 1 ), ( '?', 0 ), ( 0, 0 ),
           ( 0, 0 ) ),  # read r0 and r1 as p3 and p2, write r1 as p0
          (( 0, 3 ), ( 1, 2 ), ( 0, 0, 0 ), ( '?', 0 ), ( 0, 1 ),
           ( 0, 0 ) ),  # read r0 and r1 as p3 and p2, restoring snapshot
      ],
      dump_vcd=None,
      test_verilog=test_verilog )
