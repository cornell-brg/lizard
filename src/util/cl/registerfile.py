from pymtl import *

from util.rtl.registerfile import RegisterFileInterface


class RegisterFile:

  def __init__(s,
               dtype,
               nregs,
               num_read_ports,
               num_write_ports,
               write_read_bypass,
               write_dump_bypass,
               reset_values=None):

    s.interface = RegisterFileInterface(dtype, nregs, num_read_ports,
                                        num_write_ports, write_read_bypass,
                                        write_dump_bypass)
    s.interface.require_fl_methods(s)

  def read(s):
    pass
