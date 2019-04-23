from pymtl import *

from lizard.model.hardware_model import HardwareModel, Result
from lizard.model.flmodel import FLModel
from lizard.util.rtl.cam import Entry
from lizard.bitutil.bit_struct_generator import *


class RandomReplacementCAMFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface):
    super(RandomReplacementCAMFL, s).__init__(interface)
    nregs = s.interface.nregs
    Addr = s.interface.Addr
    Key = s.interface.Key
    Value = s.interface.Value

    s.Entry = Entry(Key, Value)
    s.state(
        entries=[s.Entry() for _ in range(nregs)],
        overwrite_counter=Addr(),
    )

    @s.model_method
    def read(key):
      for i in range(nregs - 1, -1, -1):
        entry = s.entries[i]
        if entry.key == key and entry.valid:
          return Result(value=entry.value, valid=1)
      return Result(value=s.entries[0].value, valid=0)

    @s.model_method
    def write(key, remove, value):
      new = s.Entry()
      new.key = key
      new.value = value
      if remove:
        new.valid = 0
      else:
        new.valid = 1

      last_invalid = -1
      for i in range(nregs - 1, -1, -1):
        entry = s.entries[i]
        if entry.key == key and entry.valid:
          s.entries[i] = new
          return
        if last_invalid == -1 and not entry.valid:
          last_invalid = i

      if remove:
        return

      if last_invalid != -1:
        s.entries[last_invalid] = new
      else:
        i = s.overwrite_counter
        s.entries[int(i)] = new
        if i == nregs - 1:
          s.overwrite_counter = 0
        else:
          s.overwrite_counter = i + 1
