# Author : Jacob Glueck, Christopher Batten
# Date   : Feb 28, 2019

import binascii


class SparseMemoryImage(object):

  class Section(object):

    def __init__(self, addr=0x00000000, data=bytearray()):
      self.addr = addr
      self.data = data

    def __str__(self):
      return 'addr={} data={}'.format(
          hex(self.addr), binascii.hexlify(self.data))

  def __init__(self):
    self.sections = {}

  def add_section(self, name, addr, data):
    self.sections[name] = SparseMemoryImage.Section(addr, data)

  def names(self):
    return self.sections.keys()

  def iteritems(self):
    return self.sections.iteritems()

  def __getitem__(self, name):
    return self.sections[name]

  def table(self):
    idx = 0
    result = []
    result.append('Idx Name           Addr     Size')
    for name, section in self.sections.iteritems():
      result.append('{:>3} {:<14} {:0>8x} {}'.format(idx, name, section.addr,
                                                     len(section.data)))
      idx += 1
