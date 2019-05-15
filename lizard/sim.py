#! /usr/bin/env python2

from __future__ import print_function
from util import pythonpath
import argparse
from pymtl import *
from lizard.core.rtl.proc_harness_rtl import run_mem_image
from util import elf
import sys
import os


class Proc2MngrHandler():

  def __init__(s):
    s.mode = None
    s.modes = {
        0x00010000: 'exit',
        0x00030000: 'print_int',
        0x00030001: 'print_char',
        0x00030002: 'print_string',
        0x00030003: 'print_hex',
    }

  def handle(s, msg, proc2mngr_data, curr):
    msg = int(msg)

    if s.mode is None:
      s.string_accum = ''
      s.mode = s.modes[msg]
    elif s.mode == 'exit':
      # Exit with the given status
      return msg
    elif s.mode == 'print_string':
      # Null terminated string, print
      if msg == 0:
        print(s.string_accum, end='')
        s.mode = None
      else:
        s.string_accum += chr(msg)
    elif s.mode == 'print_int':
      print(msg)
      s.mode = None
    elif s.mode == 'print_char':
      print(chr(msg), end='')
      s.mode = None
    elif s.mode == 'print_hex':
      print(hex(msg))
      s.mode = None
    else:
      raise ValueError('mode: {} is not supported'.format(s.mode))


def main():
  p = argparse.ArgumentParser(
      description="Simulate the Lizard Core running an ELF file")
  p.add_argument(
      '--trace',
      action='store_true',
      help="set to print out a line trace while the program runs")
  p.add_argument(
      '--vcd', action='store_true', help="set to generate a waveform .vcd file")
  p.add_argument(
      '--verilate',
      action='store_true',
      help="set to simulate with a verilated model")
  p.add_argument(
      '--use-cached', action='store_true', help="use a cached verilated model")
  p.add_argument(
      '--maxcycles',
      default=200000,
      type=int,
      help="maximum number of cycles to simulate")
  p.add_argument('--imem-delay', default=0, type=int, help="imem delay")
  p.add_argument('--dmem-delay', default=0, type=int, help="dmem delay")
  p.add_argument('elf_file', help="the ELF file to run")
  opts = p.parse_args()

  with open(opts.elf_file, 'rb') as ef:
    mem_image = elf.elf_reader(ef, True)

  if opts.vcd:
    elf_file_basename = os.path.basename(opts.elf_file)
    verilate_name = 'verilate' if opts.verilate else 'sim'
    name = '{}-{}.vcd'.format(elf_file_basename, verilate_name)
  else:
    name = ''

  handler = Proc2MngrHandler()
  result = run_mem_image(
      mem_image,
      opts.verilate,
      name,
      opts.maxcycles,
      handler.handle,
      opts.trace,
      use_cached_verilated=opts.use_cached,
      imem_delay=opts.imem_delay,
      dmem_delay=opts.dmem_delay)
  sys.exit(result)


if __name__ == '__main__':
  main()
