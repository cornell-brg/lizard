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
    s.state(regs=reset_values or [s.interface.Data() for _ in range(s.nregs)])

    @s.model_method
    def read(addr):
      return s.regs[addr]

    @s.model_method
    def write(addr, data):
      s.regs[addr] = data

    @s.model_method
    def dump():
      return copy_bits(s.regs)

    @s.model_method
    def set(in_):
      s.regs = copy_bits(in_)
