from pymtl import *
from core.rtl.renametable import RenameTable
from test.config import test_verilog
from method_based import create_wrapper_class, rule, st, run_state_machine_as_test, create_test_state_machine, argument_strategy, reference_precondition, MethodOrder, StrategySpec, MethodStrategy


class RenameTableWrapper:

  def __init__( s, model ):
    s.model = model
    s.model.elaborate()
    s.sim = SimulationTool( s.model )
    s.sim.reset()
    print ""

  def cycle( s ):
    s.sim.cycle()
    s.sim.print_line_trace()
    s.clear()
    s.sim.eval_combinational()

  def reset( s ):
    s.sim.reset()
    s.cycle()

  def read_ports_0__call( s, areg ):
    assert s.read_ports_0__rdy()
    s.model.read_ports[ 0 ].areg.value = areg
    s.sim.eval_combinational()
    return { 'preg': s.model.read_ports[ 0 ].preg}

  def read_ports_0__rdy( s ):
    return True

  def read_ports_1__call( s, areg ):
    assert s.read_ports_1__rdy()
    s.model.read_ports[ 1 ].areg.value = areg
    s.sim.eval_combinational()
    return { 'preg': s.model.read_ports[ 1 ].preg}

  def read_ports_1__rdy( s ):
    return True

  def write_ports_0__call( s, areg, preg ):
    assert s.write_ports_0__rdy()
    s.model.write_ports[ 0 ].call.value = 1
    s.model.write_ports[ 0 ].areg.value = areg
    s.model.write_ports[ 0 ].preg.value = preg
    s.sim.eval_combinational()

  def write_ports_0__rdy( s ):
    return True

  def snapshot_port_call( s ):
    assert s.snapshot_port_rdy()
    s.model.snapshot_port.call.value = 1
    s.sim.eval_combinational()
    return { 'id': s.model.snapshot_port.id}

  def snapshot_port_rdy( s ):
    return s.model.snapshot_port.rdy

  def restore_port_call( s, id ):
    assert s.restore_port_rdy()
    s.model.restore_port.call.value = 1
    s.model.restore_port.id.value = id
    s.sim.eval_combinational()

  def restore_port_rdy( s ):
    return True

  def free_snapshot_port_call( s, id ):
    assert s.free_snapshot_port_rdy()
    s.model.free_snapshot_port.call.value = 1
    s.model.free_snapshot_port.arg.id.value = id
    s.sim.eval_combinational()

  def free_snapshot_port_rdy( s ):
    return True

  def clear( s ):
    s.model.write_ports[ 0 ].call.value = 0
    s.model.snapshot_port.call.value = 0
    s.model.free_snapshot_port.call.value = 0
    s.model.restore_port.call.value = 0


def run_test_method_base( rename_table ):
  read_0 = rename_table.read_ports_0__call( 0 )
  read_1 = rename_table.read_ports_1__call( 1 )
  rename_table.write_ports_0__call( areg=1, preg=1 )
  assert read_0[ 'preg' ] == 3
  assert read_1[ 'preg' ] == 0
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call( 0 )
  read_1 = rename_table.read_ports_1__call( 1 )
  assert read_0[ 'preg' ] == 3
  assert read_1[ 'preg' ] == 1
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call( 0 )
  read_1 = rename_table.read_ports_1__call( 1 )
  rename_table.write_ports_0__call( 1, 2 )
  snapshot = rename_table.snapshot_port_call()
  assert read_0[ 'preg' ] == 3
  assert read_1[ 'preg' ] == 1
  assert snapshot[ 'id' ] == 0
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call( 0 )
  read_1 = rename_table.read_ports_1__call( 1 )
  rename_table.write_ports_0__call( areg=1, preg=0 )
  assert read_0[ 'preg' ] == 3
  assert read_1[ 'preg' ] == 2
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call( 0 )
  read_1 = rename_table.read_ports_1__call( 1 )
  rename_table.restore_port_call( 0 )
  assert read_0[ 'preg' ] == 3
  assert read_1[ 'preg' ] == 2
  rename_table.cycle()


def test_method_base():
  rename_table = RenameTableWrapper(
      RenameTable( 2, 4, 2, 1, 4, True, [ 0, 0 ] ) )
  run_test_method_base( rename_table )


def test_wrapper():
  model = RenameTable( 2, 4, 2, 1, 4, True, [ 0, 0 ] )
  RenameTableWrapperClass = create_wrapper_class( model )
  rename_table = RenameTableWrapperClass( model )

  run_test_method_base( rename_table )


class RenameTableStrategy( MethodStrategy ):

  def __init__( s, naregs, npregs, nsnapshots ):
    s.Areg = st.integers( min_value=0, max_value=naregs - 1 )
    s.Preg = st.integers( min_value=0, max_value=npregs - 1 )
    s.Id = st.integers( min_value=0, max_value=nsnapshots - 1 )
    s.read_ports = StrategySpec( areg=s.Areg )
    s.write_ports = StrategySpec( areg=s.Areg, preg=s.Preg )
    s.restore_port = StrategySpec( id=s.Id )
    s.free_snapshot_port = StrategySpec( id=s.Id )


class RenameTableFL:

  def __init__( s, naregs, npregs, nread_ports, nwrite_ports, nsnapshots,
                const_zero, initial_map ):
    s.strategy = RenameTableStrategy(
        naregs=naregs, npregs=npregs, nsnapshots=nsnapshots )
    s.nabits = clog2( naregs )
    s.npbits = clog2( npregs )
    s.nsbits = clog2( nsnapshots )
    s.naregs = naregs
    s.npregs = npregs
    s.nsnapshots = nsnapshots
    s.ZERO_TAG = npregs - 1
    s.initial_map = initial_map
    s.order = MethodOrder( order=[
        "restore_port", "read_ports", "write_ports", "snapshot_port",
        "free_snapshot_port"
    ] )
    s.reset()

  def reset( s ):
    s.reg_map = s.initial_map[: ]
    s.reg_map_next = []
    s.snap_shot_free_list = [ n for n in range( s.nsnapshots ) ]
    s.snap_shot = [[ 0, 0 ] for _ in range( s.nsnapshots ) ]

  def read_ports_call( s, areg ):
    assert areg < s.naregs and areg >= 0
    if areg == 0:
      return { "preg": s.ZERO_TAG}
    if s.reg_map_next:
      return { "preg": s.reg_map_next[ areg ]}
    return { "preg": s.reg_map[ areg ]}

  def read_ports_rdy( s ):
    return True

  def write_ports_call( s, areg, preg ):
    assert areg < s.naregs and areg >= 0
    assert preg < s.npregs and preg >= 0
    s.reg_map[ areg ] = preg

  def write_ports_rdy( s ):
    return True

  def snapshot_port_call( s ):
    assert s.snapshot_port_rdy()
    if not s.snap_shot_free_list:
      return { 'id': 0}

    id = s.snap_shot_free_list[ 0 ]
    s.snap_shot[ id ] = s.reg_map[: ]
    del s.snap_shot_free_list[ id ]
    return { 'id': id}

  def snapshot_port_rdy( s ):
    return len( s.snap_shot_free_list ) > 0

  def restore_port_call( s, id ):
    assert id >= 0 and id < s.nsnapshots
    assert s.restore_port_rdy()
    s.reg_map_next = s.snap_shot[ id ][: ]

  def restore_port_rdy( s ):
    return True

  @reference_precondition(
      lambda machine, data: not data[ 'id' ] in machine.reference.snap_shot_free_list
  )
  def free_snapshot_port_call( s, id ):
    assert id >= 0 and id < s.nsnapshots
    assert not id in s.snap_shot_free_list
    assert s.free_snapshot_port_rdy()
    if not id in s.snap_shot_free_list:
      s.snap_shot_free_list += [ id ]

  def free_snapshot_port_rdy( s ):
    return True

  def cycle( s ):
    if s.reg_map_next:
      s.reg_map = s.reg_map_next
      s.reg_map_next = []


def test_fl():
  rename_table = RenameTableFL( 2, 4, 2, 1, 1, True, [ 0, 0 ] )

  read_0 = rename_table.read_ports_call( 0 )
  read_1 = rename_table.read_ports_call( 1 )
  rename_table.write_ports_call( areg=1, preg=1 )
  assert read_0[ 'preg' ] == 3
  assert read_1[ 'preg' ] == 0


def test_state_machine():
  RenameTableTest = create_test_state_machine(
      RenameTable( 2, 4, 2, 1, 1, True, [ 0, 0 ] ),
      RenameTableFL( 2, 4, 2, 1, 1, True, [ 0, 0 ] ) )
  run_state_machine_as_test( RenameTableTest )
