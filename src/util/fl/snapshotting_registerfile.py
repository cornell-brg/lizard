from pymtl import *

from model.hardware_model import HardwareModel, NotReady, Result
from model.flmodel import FLModel
from util.rtl.snapshotting_registerfile import SnapshottingRegisterFileInterface
from util.fl.registerfile import RegisterFileFL
from bitutil import copy_bits


class SnapshottingRegisterFileFL(FLModel):

  @HardwareModel.validate
  def __init__(s,
               dtype,
               nregs,
               num_read_ports,
               num_write_ports,
               write_read_bypass,
               write_snapshot_bypass,
               nsnapshots,
               reset_values=None):

    super(SnapshottingRegisterFileFL, s).__init__(
        SnapshottingRegisterFileInterface(dtype, nregs, num_read_ports,
                                          num_write_ports, write_read_bypass,
                                          write_snapshot_bypass, nsnapshots))

    s.regs = RegisterFileFL(
        dtype,
        nregs,
        num_read_ports,
        num_write_ports,
        write_read_bypass,
        write_snapshot_bypass,
        reset_values=reset_values)

    s.snapshots = [
        RegisterFileFL(dtype, nregs, 0, 0, False, False)
        for _ in range(nsnapshots)
    ]

    @s.model_method
    def read(addr):
      return s.regs.read(addr)

    @s.model_method
    def write(addr, data):
      s.regs.write(addr, data)

    @s.model_method
    def set(in_):
      s.regs.set(in_)

    @s.model_method
    def snapshot(target_id):
      s.snapshots[target_id].set(s.regs.dump().out)

    @s.model_method
    def restore(source_id):
      s.regs.set(s.snapshots[source_id].dump().out)

  def _reset(s):
    s.regs.reset()
    for snapshot in s.snapshots:
      snapshot.reset()

  def _snapshot_model_state(s):
    s.regs.snapshot_model_state()
    for snapshot in s.snapshots:
      snapshot.snapshot_model_state()

  def _restore_model_state(s, state):
    s.regs.restore_model_state()
    for snapshot in s.snapshots:
      snapshot.restore_model_state()
