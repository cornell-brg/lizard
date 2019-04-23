import struct
from collections import namedtuple
from pymtl import *
from lizard.util.sparse_memory_image import SparseMemoryImage
from lizard.bitutil import data_pack_directive

PreprocessedAsm = namedtuple("Preprocessed", "text proc2mngr mngr2proc data")


class Assembler(object):

  def __init__(self, isa, text_offset, data_offset, mngr2proc_offset,
               proc2mngr_offset):
    self.isa = isa
    self.text_offset = text_offset
    self.data_offset = data_offset
    self.mngr2proc_offset = mngr2proc_offset
    self.proc2mngr_offset = proc2mngr_offset

  def preprocess_asm(self, seq_list):
    """
    Takes a list of instructions, and:
    1. Removes all comments, blank lines, or other useless information
    2. Seperates into 4 sections: .text, .proc2mngr, .mngr2proc, and .data
    3. Expands pseudo instructions
    Returns: a PreprocessedAsm namedtuple with a list of source lines for each section
    """

    text = []
    proc2mngr = []
    mngr2proc = []
    data = []

    in_data = False
    current = text

    for line in seq_list.splitlines():
      line = line.partition('#')[0].strip()
      if len(line) == 0:
        continue

      if ':' in line:
        current.append(line)
      elif line == ".data":
        assert not in_data
        in_data = True
        current = data
      elif not in_data:
        aux = None
        if '<' in line:
          line, value = line.split('<')
          aux = mngr2proc
        elif '>' in line:
          line, value = line.split('>')
          aux = proc2mngr
        if aux is not None:
          aux.append(int(Bits(self.isa.xlen, int(value.strip(), 0))))
          line = line.strip()
        current += self.isa.expand_pseudo_instructions(line)
      else:
        current += [line]

    return PreprocessedAsm(text, proc2mngr, mngr2proc, data)

  def augment_symbol_table(self, base, code, sym):
    addr = base
    result = []
    for line in code:
      if ':' in line:
        line, extra = line.split(':', 1)
        assert len(extra) == 0
        line = line.strip()
        assert line not in sym
        sym[line] = addr
      else:
        result.append(line)
        addr += self.isa.ilen_bytes
    return result

  def assemble(self, asm_code):
    assert isinstance(asm_code, str)

    asm_list = self.preprocess_asm(asm_code)
    sym = {}
    asm_list = asm_list._replace(
        text=self.augment_symbol_table(self.text_offset, asm_list.text, sym),
        data=self.augment_symbol_table(self.data_offset, asm_list.data, sym))

    asm_list_idx = 0
    text_bytes = bytearray()
    mngr2proc_bytes = bytearray()
    proc2mngr_bytes = bytearray()
    data_bytes = bytearray()

    addr = self.text_offset
    for line in asm_list.text:
      bits = self.isa.assemble_inst(sym, addr, line)
      text_bytes.extend(struct.pack("<I", bits.uint()))
      addr += self.isa.ilen_bytes

    for value in asm_list.mngr2proc:
      mngr2proc_bytes.extend(
          struct.pack(data_pack_directive(self.isa.xlen), value))
    for value in asm_list.proc2mngr:
      proc2mngr_bytes.extend(
          struct.pack(data_pack_directive(self.isa.xlen), value))

    for line in asm_list.data:
      # only support .word because:
      # 1. labels inside are easier to compute
      # 2. no alignment issues. .word is supposed to align on a natrual
      #    boundary, which takes no effort if everything is a word.
      assert line.startswith(".word")
      _, value = line.split()
      data_bytes.extend(struct.pack("<I", int(value, 0)))

    mem_image = SparseMemoryImage()
    if len(text_bytes) > 0:
      mem_image.add_section(".text", self.text_offset, text_bytes)
    if len(mngr2proc_bytes) > 0:
      mem_image.add_section(".mngr2proc", self.mngr2proc_offset,
                            mngr2proc_bytes)
    if len(proc2mngr_bytes) > 0:
      mem_image.add_section(".proc2mngr", self.proc2mngr_offset,
                            proc2mngr_bytes)
    if len(data_bytes) > 0:
      mem_image.add_section(".data", self.data_offset, data_bytes)

    return mem_image

  def disassemble(self, mem_image):
    text_section = mem_image.get_section(".text")
    addr = text_section.addr
    asm_code = ""
    for i in xrange(0, len(text_section.data), self.isa.ilen_bytes):
      bits = struct.unpack_from(
          "<I", buffer(text_section.data, i, self.isa.ilen_bytes))[0]
      inst_str = self.isa.disassemble_inst(Bits(self.isa.ilen_bytes * 8, bits))
      disasm_line = " {:0>8x}  {:0>8x}  {}\n".format(addr + i, bits, inst_str)
      asm_code += disasm_line

    return asm_code
