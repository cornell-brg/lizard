from pymtl import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.cl import InValRdyQueueAdapter, OutValRdyQueueAdapter

from config.general import *
from util.method_test import ReturnValues, DefineMethod, create_wrapper_class, rule, st, run_state_machine, create_test_state_machine, argument_strategy, reference_precondition, MethodOrder, ArgumentStrategy, MethodStrategy, generate_methods_from_model, bits_strategy
from util.test_utils import run_rdycall_test_vector_sim
from util.fl.freelist import FreeListFL
from util.rtl.method import MethodSpec
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface, PregState
from renametable_method_test import RenameTableStrategy, RenameTableFL
from test.config import test_verilog
from msg.codes import *


class PregState(BitStructDefinition):

  def __init__(s):
    s.value = BitField(XLEN)
    s.ready = BitField(1)
    s.areg = BitField(AREG_IDX_NBITS)


class DataFlowManagerStrategy(MethodStrategy):

  def __init__(s, naregs, npregs, nsnapshots):
    s.rename_table_strategy = RenameTableStrategy(naregs, npregs, nsnapshots)
    s.Areg = s.rename_table_strategy.Areg
    s.Preg = s.rename_table_strategy.Preg

    s.Value = bits_strategy(XLEN)
    s.Csr_num = bits_strategy(CSR_SPEC_NBITS)

    s.restore_port = s.rename_table_strategy.restore_port
    s.free_snapshot_port = s.rename_table_strategy.free_snapshot_port

    s.rollback = ArgumentStrategy()
    s.get_src_ports = ArgumentStrategy(areg=s.Areg)
    s.get_dst_ports = ArgumentStrategy(areg=s.Areg)
    s.read_tag_ports = ArgumentStrategy(tag=s.Preg)
    s.write_tag_ports = ArgumentStrategy(tag=s.Preg, value=s.Value)
    s.free_tag_ports = ArgumentStrategy(tag=s.Preg, commit=bits_strategy(1))
    s.read_csr_port = ArgumentStrategy(csr_num=s.Csr_num)
    s.write_csr_port = ArgumentStrategy(csr_num=s.Csr_num, value=s.Value)


# TODO
# generate_methods_from_model( DataFlowManager( 2, 2 ) )


class DataFlowManagerFL:

  def __init__(s, num_src_ports, num_dst_ports):
    s.strategy = DataFlowManagerStrategy(AREG_COUNT, PREG_COUNT, MAX_SPEC_DEPTH)
    s.order = MethodOrder(order=[
        "rollback_port", "restore_port", "get_src_ports", "get_dst_ports",
        "write_tag_ports", "read_tag_ports", "snapshot_port",
        "free_snapshot_port", "free_tag_ports"
    ])

    s.free_regs = FreeListFL(PREG_COUNT - 1)
    s.zero_tag = Bits(PREG_IDX_NBITS, PREG_COUNT - 1)

    initial_map = [0] + [x for x in range(AREG_COUNT - 1)]
    s.rename_table = RenameTableFL(AREG_COUNT, PREG_COUNT, num_src_ports,
                                   num_dst_ports, MAX_SPEC_DEPTH, True,
                                   initial_map)

    s.preg_file = [PregState() for _ in range(PREG_COUNT)]
    s.areg_file = [Bits(PREG_IDX_NBITS) for _ in range(AREG_COUNT)]
    s.mngr2proc = InValRdyBundle(Bits(XLEN))
    s.proc2mngr = OutValRdyBundle(Bits(XLEN))

    # size of None means it can grow arbitraily large
    s.mngr2proc_q = InValRdyQueueAdapter(s.mngr2proc, size=None)
    s.proc2mngr_q = OutValRdyQueueAdapter(s.proc2mngr, size=None)
    s.reset()

  def free_snapshot_port_call(s, id):
    s.rename_table.free_snapshot_port_call(id)

  def free_tag_ports_call(s, commit, tag):
    if tag != s.zero_tag:
      if commit:
        preg = s.preg_file[tag]
        if preg.areg != 0:
          s.free_regs.free(s.areg_file[preg.areg])
          s.areg_file[preg.areg] = tag
      else:
        s.free_regs.free(tag)

  def get_dst_ports_call(s, areg):
    resp = ReturnValues()
    if areg != 0:
      preg = s.free_regs.alloc()
      if preg is None:
        resp.success = 0
        resp.tag = "?"
      else:
        resp.success = 1
        resp.tag = preg
        s.rename_table.write_ports_call(areg, preg)
        preg_entry = s.preg_file[preg]
        preg_entry.ready = 0
        preg_entry.areg = areg
    else:
      resp.success = 1
      resp.tag = s.zero_tag
    return resp

  def get_src_ports_call(s, areg):
    resp = ReturnValues()
    if areg != 0:
      resp.preg = s.rename_table.read_ports_call(areg).preg
    else:
      resp.preg = s.zero_tag
    return resp

  def read_csr_port_call(s, csr_num):
    if csr_num == CsrRegisters.mngr2proc:
      if s.mngr2proc_q.empty():
        return ("?", 0)
      else:
        return (s.mngr2proc_q.deq(), 1)
    else:
      # no other CSRs supported
      return (0, 1)

  def read_tag_ports_call(s, tag):
    resp = ReturnValues()
    if tag != s.zero_tag:
      assert (int(tag) != int(s.zero_tag))
      preg = s.preg_file[tag]
      resp.ready = preg.ready
      if not preg.ready:
        resp.value = "?"
      else:
        resp.value = preg.value
    else:
      resp.ready = 1
      resp.value = 0
    return resp

  def restore_port_call(s, id):
    s.rename_table.restore_port_call(id)

  def rollback_port_call(s):
    s.rename_table.set_external_restore_call(s.areg_file)

  def snapshot_port_call(s):
    assert s.snapshot_port_rdy()
    return s.rename_table.snapshot_port_call()

  def snapshot_port_rdy(s):
    return s.rename_table.snapshot_port_rdy()

  def write_csr_port_call(s, csr_num, value):
    resp = ReturnValues()
    if csr_num == CsrRegisters.proc2mngr:
      # can grow forever, so enq will always work
      s.proc2mngr_q.enq(value)
      resp.success = 1
    else:
      # no other CSRs supported
      resp.success = 1
    return resp

  def write_tag_ports_call(s, tag, value):
    if tag != s.zero_tag:
      preg = s.preg_file[tag]
      preg.value = value
      preg.ready = 1

  def reset(s):
    print "reset"
    s.free_regs.reset = 1
    s.free_regs.xtick()
    s.rename_table.reset()
    s.preg_file = [PregState() for _ in range(PREG_COUNT)]
    s.areg_file = [0] + [x for x in range(AREG_COUNT - 1)]
    for areg in range(AREG_COUNT):
      tag = s.get_dst_ports_call(areg).tag
      s.write_tag_ports_call(tag, 0)

  def cycle(s):
    s.rename_table.cycle()
    s.free_regs.reset = 0
    s.free_regs.xtick()
    s.forwards = dict()
    #s.mngr2proc_q.xtick()
    #s.proc2mngr_q.xtick()


def test_state_machine():

  DataFlowTest = create_test_state_machine(
      DataFlowManager(1, 1), DataFlowManagerFL(1, 1))
  run_state_machine(DataFlowTest)
