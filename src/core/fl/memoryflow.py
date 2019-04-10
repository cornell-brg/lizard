from pymtl import *

from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from util.fl.overlap_checker import OverlapCheckerFL, OverlapCheckerInterface
from util.fl.registerfile import RegisterFileFL
from core.rtl.memoryflow import StoreSpec


class MemoryFlowManagerFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, MemMsg):
    super(MemoryFlowManagerFL, s).__init__(interface)
    s.state(
        store_table=RegisterFileFL(
            StoreSpec(s.interface.Addr.nbits, s.interface.Size.nbits),
            s.interface.nslots, 1, 1, False, False),
        valid_table=RegisterFileFL(
            Bits(1), s.interface.nslots, 0, 2, False, False,
            [0] * s.interface.nslots),
        overlap_checker=OverlapCheckerFL(
            OverlapCheckerInterface(s.interface.Addr.nbits,
                                    s.interface.max_size)),
    )

    @s.model_method
    def store_pending(live_mask, addr, size):
      live_mask = Bits(s.interface.nslots, int(live_mask))
      dump = s.store_table.dump().out
      valid_dump = s.valid_table.dump().out
      for i in range(s.interface.nslots):
        disjoint = s.overlap_checker.check(addr, size, dump[i].addr,
                                           dump[i].size).disjoint
        if not disjoint and live_mask[i] and valid_dump[i]:
          return 1
      return 0

    @s.model_method
    def register_store(id_):
      s.valid_table.write(addr=id_, data=0)

    @s.model_method
    def enter_store(id_, addr, size, data):
      spec = StoreSpec(s.interface.Addr.nbits, s.interface.Size.nbits)
      spec.addr = addr
      spec.size = size
      s.store_table.write(addr=id_, data=spec)
      s.valid_table.write(addr=id_, data=1)
