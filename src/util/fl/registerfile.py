from pymtl import *

from model.hardware_model import HardwareModel, NotReady, Result
from model.flmodel import FLModel
from util.rtl.registerfile import RegisterFileInterface
from bitutil import copy_bits


class RegisterFileFL(FLModel):

  @HardwareModel.validate
  def __init__(s,
               dtype,
               nregs,
               num_read_ports,
               num_write_ports,
               write_read_bypass,
               write_dump_bypass,
               reset_values=None):
    super(RegisterFileFL, s).__init__(
        RegisterFileInterface(dtype, nregs, num_read_ports, num_write_ports,
                              write_read_bypass, write_dump_bypass))
    s.nregs = nregs
    s.reset_values = reset_values or [
        s.interface.Data() for _ in range(s.nregs)
    ]

    @s.model_method
    def read(addr):
      return s.regs[addr]

    @s.model_method
    def write(addr, data):
      s.regs[addr] = data

    @s.model_method
    def dump():
      return s.regs[:]

    @s.model_method
    def set(in_):
      s.regs = in_[:]

  def _reset(s):
    s.regs = s.reset_values

  def _snapshot_model_state(s):
    return [copy_bits(x) for x in s.regs]

  def _restore_model_state(s, state):
    s.regs = [copy_bits(x) for x in state]
