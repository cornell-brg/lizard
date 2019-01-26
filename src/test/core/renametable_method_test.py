from pymtl import *
from core.rtl.renametable import RenameTable
from test.config import test_verilog
from util.method_test import DefineMethod, ReturnValues, create_wrapper_class, rule, st, run_state_machine, create_test_state_machine, argument_strategy, reference_precondition, MethodOrder, ArgumentStrategy, MethodStrategy


#-------------------------------------------------------------------------
# RenameTableWrapper
#-------------------------------------------------------------------------
class RenameTableWrapper:

  def __init__(s, model):
    s.model = model
    s.model.elaborate()
    s.sim = SimulationTool(s.model)
    s.sim.reset()
    print ""

  def cycle(s):
    s.sim.cycle()
    s.sim.print_line_trace()
    s.clear()
    s.sim.eval_combinational()

  def reset(s):
    s.sim.reset()
    s.cycle()

  def read_ports_0__call(s, areg):
    s.model.read_ports[0].areg.value = areg
    s.sim.eval_combinational()
    return {'preg': s.model.read_ports[0].preg}

  def read_ports_1__call(s, areg):
    s.model.read_ports[1].areg.value = areg
    s.sim.eval_combinational()
    return {'preg': s.model.read_ports[1].preg}

  def write_ports_0__call(s, areg, preg):
    s.model.write_ports[0].call.value = 1
    s.model.write_ports[0].areg.value = areg
    s.model.write_ports[0].preg.value = preg
    s.sim.eval_combinational()

  def snapshot_port_call(s):
    assert s.snapshot_port_rdy()
    s.model.snapshot_port.call.value = 1
    s.sim.eval_combinational()
    return {'id': s.model.snapshot_port.id}

  def snapshot_port_rdy(s):
    return s.model.snapshot_port.rdy

  def restore_port_call(s, id):
    s.model.restore_port.call.value = 1
    s.model.restore_port.id.value = id
    s.sim.eval_combinational()

  def free_snapshot_port_call(s, id):
    s.model.free_snapshot_port.call.value = 1
    s.model.free_snapshot_port.arg.id.value = id
    s.sim.eval_combinational()

  def set_external_restore_call(s, external_restore):
    assert len(external_restore) == 4
    s.model.external_restore_en.v = 1
    for x in range(2):
      s.model.external_restore_in[x].v = external_restore[x]
    s.sim.eval_combinational()

  def clear(s):
    s.model.write_ports[0].call.value = 0
    s.model.snapshot_port.call.value = 0
    s.model.free_snapshot_port.call.value = 0
    s.model.restore_port.call.value = 0
    s.model.external_restore_en.v = 0


#-------------------------------------------------------------------------
# run_method_test
#-------------------------------------------------------------------------
def run_method_test(rename_table):
  read_0 = rename_table.read_ports_0__call(0)
  read_1 = rename_table.read_ports_1__call(1)
  rename_table.write_ports_0__call(areg=1, preg=1)
  assert read_0['preg'] == 3
  assert read_1['preg'] == 0
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call(0)
  read_1 = rename_table.read_ports_1__call(1)
  assert read_0['preg'] == 3
  assert read_1['preg'] == 1
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call(0)
  read_1 = rename_table.read_ports_1__call(1)
  rename_table.write_ports_0__call(1, 2)
  snapshot = rename_table.snapshot_port_call()
  assert read_0['preg'] == 3
  assert read_1['preg'] == 1
  assert snapshot['id'] == 0
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call(0)
  read_1 = rename_table.read_ports_1__call(1)
  rename_table.write_ports_0__call(areg=1, preg=0)
  assert read_0['preg'] == 3
  assert read_1['preg'] == 2
  rename_table.cycle()

  read_0 = rename_table.read_ports_0__call(0)
  read_1 = rename_table.read_ports_1__call(1)
  rename_table.restore_port_call(0)
  assert read_0['preg'] == 3
  assert read_1['preg'] == 2
  rename_table.cycle()

  rename_table.set_external_restore_call([2, 1, 2, 3])
  rename_table.restore_port_call(1)
  read_0 = rename_table.read_ports_0__call(0)
  read_1 = rename_table.read_ports_1__call(1)
  assert read_0['preg'] == 3
  assert read_1['preg'] == 1
  rename_table.cycle()


#-------------------------------------------------------------------------
# test_method
#-------------------------------------------------------------------------
def test_method():
  rename_table = RenameTableWrapper(
      RenameTable(4, 4, 2, 1, 4, True, [0, 0, 0, 0]))
  run_method_test(rename_table)


#-------------------------------------------------------------------------
# test_wrapper
#-------------------------------------------------------------------------
def test_wrapper():
  model = RenameTable(4, 4, 2, 1, 4, True, [0, 0, 0, 0])

  def set_external_restore_call(s, external_restore):
    assert len(external_restore) == 4
    s.model.external_restore_en.v = 1
    for x in range(4):
      s.model.external_restore_in[x].v = external_restore[x]
    s.sim.eval_combinational()

  def clear_set_external_restore(s):
    s.model.external_restore_en.v = 0

  RenameTableWrapperClass, method_specs = create_wrapper_class(
      model,
      customized_methods=[
          DefineMethod(
              method_call=set_external_restore_call,
              method_name="set_external_restore",
              arg={"external_restore": list},
              method_clear=clear_set_external_restore)
      ])

  rename_table = RenameTableWrapperClass(model)

  run_method_test(rename_table)


#-------------------------------------------------------------------------
# RenameTableStrategy
#-------------------------------------------------------------------------
class RenameTableStrategy(MethodStrategy):

  def __init__(s, naregs, npregs, nsnapshots):
    s.Areg = st.integers(min_value=0, max_value=naregs - 1)
    s.Preg = st.integers(min_value=0, max_value=npregs - 1)
    s.Id = st.integers(min_value=0, max_value=nsnapshots - 1)
    s.read_ports = ArgumentStrategy(areg=s.Areg)
    s.write_ports = ArgumentStrategy(areg=s.Areg, preg=s.Preg)
    s.restore_port = ArgumentStrategy(id=s.Id)
    s.free_snapshot_port = ArgumentStrategy(id=s.Id)
    s.set_external_restore = ArgumentStrategy(
        external_restore=st.lists(
            elements=s.Preg, min_size=naregs, max_size=naregs))


#-------------------------------------------------------------------------
# RenameTableFL
#-------------------------------------------------------------------------
class RenameTableFL:

  def __init__(s, naregs, npregs, nread_ports, nwrite_ports, nsnapshots,
               const_zero, initial_map):
    s.strategy = RenameTableStrategy(
        naregs=naregs, npregs=npregs, nsnapshots=nsnapshots)
    s.nabits = clog2(naregs)
    s.npbits = clog2(npregs)
    s.nsbits = clog2(nsnapshots)
    s.naregs = naregs
    s.npregs = npregs
    s.nsnapshots = nsnapshots
    s.ZERO_TAG = npregs - 1
    s.initial_map = initial_map
    s.order = MethodOrder(order=[
        "set_external_restore", "restore_port", "read_ports", "write_ports",
        "snapshot_port", "free_snapshot_port"
    ])
    s.reset()

  def reset(s):
    s.reg_map = s.initial_map[:]
    s.reg_map_next = []
    s.external_restore = []
    s.snap_shot_free_list = [1 for n in range(s.nsnapshots)]
    s.snap_shot = [[0 for _ in range(s.naregs)] for _ in range(s.nsnapshots)]

  def read_ports_call(s, areg):
    assert areg < s.naregs and areg >= 0
    if areg == 0:
      return ReturnValues(preg=s.ZERO_TAG)
    if s.reg_map_next:
      return ReturnValues(preg=s.reg_map_next[areg])
    return ReturnValues(preg=s.reg_map[areg])

  def write_ports_call(s, areg, preg):
    assert areg < s.naregs and areg >= 0
    assert preg < s.npregs and preg >= 0
    s.reg_map[areg] = preg

  def snapshot_port_call(s):
    assert s.snapshot_port_rdy()
    for i in range(len(s.snap_shot_free_list)):
      if s.snap_shot_free_list[i]:
        s.snap_shot_free_list[i] = 0
        id = i
        break

    s.snap_shot[id] = s.reg_map[:]
    return ReturnValues(id=id)

  def snapshot_port_rdy(s):
    return not all(not i for i in s.snap_shot_free_list)

  def restore_port_call(s, id):
    assert id >= 0 and id < s.nsnapshots
    if s.external_restore:
      s.reg_map_next = s.external_restore[:]
    else:
      s.reg_map_next = s.snap_shot[id][:]

  def free_snapshot_port_call(s, id):
    assert id >= 0 and id < s.nsnapshots
    s.snap_shot_free_list[id] = 1

  def set_external_restore_call(s, external_restore):
    s.external_restore = external_restore

  def cycle(s):
    if s.reg_map_next:
      s.reg_map = s.reg_map_next
      s.reg_map_next = []
    s.external_restore = []


#-------------------------------------------------------------------------
# test_fl
#-------------------------------------------------------------------------
def test_fl():
  rename_table = RenameTableFL(4, 4, 2, 1, 1, True, [0, 0, 0, 0])

  read_0 = rename_table.read_ports_call(0)
  read_1 = rename_table.read_ports_call(1)
  rename_table.write_ports_call(areg=1, preg=1)
  assert read_0.preg == 3
  assert read_1.preg == 0


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():

  def set_external_restore_call(s, external_restore):
    assert len(external_restore) == 4
    s.model.external_restore_en.v = 1
    for x in range(4):
      s.model.external_restore_in[x].v = external_restore[x]
    s.sim.eval_combinational()

  def clear_set_external_restore(s):
    s.model.external_restore_en.v = 0

  RenameTableTest = create_test_state_machine(
      RenameTable(4, 4, 2, 1, 2, True, [0, 0, 0, 0]),
      RenameTableFL(4, 4, 2, 1, 2, True, [0, 0, 0, 0]),
      customized_methods=[
          DefineMethod(
              method_call=set_external_restore_call,
              method_name="set_external_restore",
              arg={"external_restore": list},
              method_clear=clear_set_external_restore)
      ])
  run_state_machine(RenameTableTest)
