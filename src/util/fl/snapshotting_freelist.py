from pymtl import *

from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from util.fl.freelist import FreeListFL
from util.rtl.snapshotting_freelist import SnapshottingFreeListInterface
from bitutil import copy_bits


class SnapshottingFreeListFL(FLModel):

  def __init__(s,
               nslots,
               num_alloc_ports,
               num_free_ports,
               nsnapshots,
               used_slots_initial=0):
    super(SnapshottingFreeListFL, s).__init__(
        SnapshottingFreeListInterface(nslots, num_alloc_ports, num_free_ports,
                                      nsnapshots))

    s.nslots = nslots
    s.zero_snapshot = [Bits(nslots) for _ in range(nsnapshots)]
    s.nsnapshots = nsnapshots

    s.state(
        freelist=FreeListFL(
            nslots,
            num_alloc_ports,
            num_free_ports,
            free_alloc_bypass=False,
            release_alloc_bypass=False,
            used_slots_initial=used_slots_initial),
        snapshots=copy_bits(s.zero_snapshot))

    def pack(snapshot):
      return res

    @s.model_method
    def get_state():
      return s.freelist.get_state()

    @s.ready_method
    def alloc():
      return s.freelist.alloc.rdy()

    @s.model_method
    def alloc():
      result = s.freelist.alloc()
      for i in range(s.nsnapshots):
        s.snapshots[i][result.index] = 1
      return result

    @s.model_method
    def free(index):
      s.freelist.free(index)

    @s.model_method
    def reset_alloc_tracking(target_id):
      s.snapshots[target_id] = copy_bits(s.zero_snapshot[0])

    @s.model_method
    def revert_allocs(source_id):
      packed = Bits(s.nslots)
      for i in range(s.nslots):
        packed[i] = s.snapshots[source_id][i]
      s.freelist.release(packed)

    @s.model_method
    def set(state):
      s.freelist.set(state)
