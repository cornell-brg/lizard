from pymtl import *

from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from core.rtl.renametable import RenameTableInterface
from util.fl.snapshotting_registerfile import SnapshottingRegisterFileFL
from bitutil import copy_bits


class RenameTableFL(FLModel):

  @HardwareModel.validate
  def __init__(s, naregs, npregs, num_lookup_ports, num_update_ports,
               nsnapshots, const_zero, initial_map):
    super(RenameTableFL, s).__init__(
        RenameTableInterface(naregs, npregs, num_lookup_ports, num_update_ports,
                             nsnapshots))

    s.rename_table = SnapshottingRegisterFileFL(
        s.interface.Preg,
        naregs,
        num_lookup_ports,
        num_update_ports,
        False,
        True,
        nsnapshots,
        reset_values=initial_map)

    if const_zero:
      s.ZERO_TAG = Bits(s.interface.Preg.nbits, npregs - 1)

    @s.model_method
    def lookup(areg):
      if const_zero and areg == 0:
        return s.ZERO_TAG
      else:
        return s.rename_table.read(areg).data

    @s.model_method
    def update(areg, preg):
      if const_zero and areg == 0:
        pass
      else:
        s.rename_table.write(addr=areg, data=preg)

    @s.model_method
    def snapshot(target_id):
      s.rename_table.snapshot(target_id)

    @s.model_method
    def restore(source_id):
      s.rename_table.restore(source_id)

    @s.model_method
    def set(in_):
      s.rename_table.set(in_)

  def _reset(s):
    s.rename_table.reset()

  def _snapshot_model_state(s):
    s.rename_table._snapshot_model_state()

  def _restore_model_state(s, state):
    s.rename_table._restore_model_state()
