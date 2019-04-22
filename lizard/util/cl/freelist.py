from pymtl import *
from lizard.bitutil import clog2


class FreeListCL(Model):

  def __init__(self, nslots):

    self.nbits = clog2(nslots)
    # 1 if free 0 otherwise
    self.free_list = [Bits(1) for _ in range(nslots)]

  def xtick(self):
    if self.reset:
      for x in range(len(self.free_list)):
        self.free_list[x] = Bits(1, 1)

  # Returns either the tag or None if full
  def alloc(self):
    for i in range(len(self.free_list)):
      if self.free_list[i] == 1:
        self.free_list[i] = 0
        return Bits(self.nbits, i)

    return None

  def free(self, tag):
    self.free_list[tag] = 1

  def line_trace(self):
    return str(self)

  def __str__(self):
    return ''.join([str(x) for x in self.free_list])
