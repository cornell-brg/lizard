#=========================================================================
# tinyrv2_encoding
#=========================================================================
# This module encapsulates the encoding of the TinyRV2 instruction set and
# includes assembly/disassembly functions. We first define a TinyRV2
# encoding table which includes instruction templates and opcode
# mask/match bits. We then define assembly/dissassembly functions for
# each field. Finally, we use the encoding table and assembly/disassembly
# field functions to create the assembly/disassembly instructions for
# single instructions and as well as for small programs.
#
# Author : Christopher Batten, Shunning Jiang
# Date   : Aug 27, 2016

import struct

from pymtl import Bits, concat
from string import translate, maketrans
from util.sparse_memory_image import SparseMemoryImage
from config.general import *
from msg.codes import *

#=========================================================================
# Encoding Table
#=========================================================================
# There should be one row in the table for each instruction. The row
# should have three columns corresponding to: instruction template,
# opcode mask, and opcode match. The instruction template should start
# with the instruction name and a list of field tags deliminted by
# whitespace, commas, and/or parentheses. The field tags should map to
# assemble_field and disasm_field functions below. The instruction
# template is used both for assembly and disassembly. The opcode
# mask/match columns are used for decoding; effectively an encoded
# instruction is tested against each entry in the table by first applying
# the mask and then checking for a match.

tinyrv2_encoding_table = \
[

    # inst                           opcode mask                         opcode
    # pseudo
    [ "nop",                         0b11111111111111111111111111111111, 0b00000000000000000000000000010011 ],
    [ "j      j_imm",                0b00000000000000000000111111111111, 0b00000000000000000000000001101111 ], # UJ-type
    [ "csrr    rd, csrnum",          0b00000000000011111111000001111111, 0b00000000000000000010000001110011 ], # I-type, csrrs
    [ "csrw    csrnum, rs1",         0b00000000000000000111111111111111, 0b00000000000000000001000001110011 ], # I-type, csrrw

    # lui
    [ "lui    rd, u_imm",            0b00000000000000000000000001111111, 0b00000000000000000000000000110111 ], # U-type

    # auipc
    [ "auipc  rd, u_imm",            0b00000000000000000000000001111111, 0b00000000000000000000000000010111 ], # U-type

    # jal
    [ "jal    rd, j_imm",            0b00000000000000000000000001111111, 0b00000000000000000000000001101111 ], # UJ-type
    [ "jalr   rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000000000001100111 ], # I-type

    # branch
    [ "beq    rs1, rs2, b_imm",      0b00000000000000000111000001111111, 0b00000000000000000000000001100011 ], # SB-type
    [ "bne    rs1, rs2, b_imm",      0b00000000000000000111000001111111, 0b00000000000000000001000001100011 ], # SB-type
    [ "blt    rs1, rs2, b_imm",      0b00000000000000000111000001111111, 0b00000000000000000100000001100011 ], # SB-type
    [ "bge    rs1, rs2, b_imm",      0b00000000000000000111000001111111, 0b00000000000000000101000001100011 ], # SB-type
    [ "bltu   rs1, rs2, b_imm",      0b00000000000000000111000001111111, 0b00000000000000000110000001100011 ], # SB-type
    [ "bgeu   rs1, rs2, b_imm",      0b00000000000000000111000001111111, 0b00000000000000000111000001100011 ], # SB-type

    # load
    [ "lb     rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000000000000000011 ], # I-type
    [ "lh     rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000001000000000011 ], # I-type
    [ "lw     rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000010000000000011 ], # I-type
    [ "ld     rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000011000000000011 ], # I-type
    [ "lbu    rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000100000000000011 ], # I-type
    [ "lhu    rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000101000000000011 ], # I-type
    [ "lwu    rd, i_imm(rs1)",       0b00000000000000000111000001111111, 0b00000000000000000110000000000011 ], # I-type

    # store
    [ "sb     rs2, s_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000000000000100011 ], # S-type
    [ "sh     rs2, s_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000001000000100011 ], # S-type
    [ "sw     rs2, s_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000010000000100011 ], # S-type
    [ "sd     rs2, s_imm(rs1)",      0b00000000000000000111000001111111, 0b00000000000000000011000000100011 ], # S-type

    # rimm
    [ "addi   rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000000000000010011 ], # I-type
    [ "slti   rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000010000000010011 ], # I-type
    [ "sltiu  rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000011000000010011 ], # I-type
    [ "xori   rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000100000000010011 ], # I-type
    [ "ori    rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000110000000010011 ], # I-type
    [ "andi   rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000111000000010011 ], # I-type
    [ "slli   rd, rs1, shamt",       0b11111100000000000111000001111111, 0b00000000000000000001000000010011 ], # R-type
    [ "srli   rd, rs1, shamt",       0b11111100000000000111000001111111, 0b00000000000000000101000000010011 ], # R-type
    [ "srai   rd, rs1, shamt",       0b11111100000000000111000001111111, 0b01000000000000000101000000010011 ], # R-type

    [ "addiw  rd, rs1, i_imm",       0b00000000000000000111000001111111, 0b00000000000000000000000000011011 ], # I-type
    [ "slliw  rd, rs1, shamt",       0b11111110000000000111000001111111, 0b00000000000000000001000000011011 ], # R-type
    [ "srliw  rd, rs1, shamt",       0b11111110000000000111000001111111, 0b00000000000000000101000000011011 ], # R-type
    [ "sraiw  rd, rs1, shamt",       0b11111110000000000111000001111111, 0b01000000000000000101000000011011 ], # R-type

    # rr
    [ "add    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000000000000110011 ], # R-type
    [ "sub    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b01000000000000000000000000110011 ], # R-type
    [ "sll    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000001000000110011 ], # R-type
    [ "slt    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000010000000110011 ], # R-type
    [ "sltu   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000011000000110011 ], # R-type
    [ "xor    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000100000000110011 ], # R-type
    [ "srl    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000101000000110011 ], # R-type
    [ "sra    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b01000000000000000101000000110011 ], # R-type
    [ "or     rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000110000000110011 ], # R-type
    [ "and    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000111000000110011 ], # R-type

    [ "addw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000000000000111011 ], # R-type
    [ "subw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b01000000000000000000000000111011 ], # R-type
    [ "sllw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000001000000111011 ], # R-type
    [ "srlw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000000000000000101000000111011 ], # R-type
    [ "sraw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b01000000000000000101000000111011 ], # R-type

    # fence
    [ "fence   pred, succ",          0b11110000000011111111111111111111, 0b00000000000000000000000000001111 ],
    [ "fence.i",                     0b11111111111111111111111111111111, 0b00000000000000000001000000001111 ],

    # system
    [ "ecall",                       0b11111111111111111111111111111111, 0b00000000000000000000000001110011 ],
    [ "ebreak",                      0b11111111111111111111111111111111, 0b00000000000100000000000001110011 ],
    [ "csrrw   rd, csrnum, rs1",     0b00000000000000000111000001111111, 0b00000000000000000001000001110011 ], # I-type, csrrw
    [ "csrrs   rd, csrnum, rs1",     0b00000000000000000111000001111111, 0b00000000000000000010000001110011 ], # I-type, csrrs
    [ "csrrc   rd, csrnum, rs1",     0b00000000000000000111000001111111, 0b00000000000000000011000001110011 ], # I-type, csrrc
    [ "csrrwi  rd, csrnum, c_imm",   0b00000000000000000111000001111111, 0b00000000000000000101000001110011 ], # I-type, csrrw
    [ "csrrsi  rd, csrnum, c_imm",   0b00000000000000000111000001111111, 0b00000000000000000110000001110011 ], # I-type, csrrs
    [ "csrrci  rd, csrnum, c_imm",   0b00000000000000000111000001111111, 0b00000000000000000111000001110011 ], # I-type, csrrc

    # multiply
    [ "mul    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000000000000110011 ], # R-type
    [ "mulh   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000001000000110011 ], # R-type
    [ "mulhsu rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000010000000110011 ], # R-type
    [ "mulhu  rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000011000000110011 ], # R-type
    [ "div    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000100000000110011 ], # R-type
    [ "divu   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000101000000110011 ], # R-type
    [ "rem    rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000110000000110011 ], # R-type
    [ "remu   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000111000000110011 ], # R-type

    [ "mulw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000000000000111011 ], # R-type
    [ "divw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000100000000111011 ], # R-type
    [ "divuw  rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000101000000111011 ], # R-type
    [ "remw   rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000110000000111011 ], # R-type
    [ "remuw  rd, rs1, rs2",         0b11111110000000000111000001111111, 0b00000010000000000111000000111011 ], # R-type

    # atomic
    [ "lr.w           rd, rs1",           0b11111111111100000111000001111111, 0b00010000000000000010000000101111 ],
    [ "lr.w.aq        rd, rs1",           0b11111111111100000111000001111111, 0b00010100000000000010000000101111 ],
    [ "lr.w.rl        rd, rs1",           0b11111111111100000111000001111111, 0b00010010000000000010000000101111 ],
    [ "lr.w.aqrl      rd, rs1",           0b11111111111100000111000001111111, 0b00010110000000000010000000101111 ],
    [ "sc.w           rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011000000000000010000000101111 ],
    [ "sc.w.aq        rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011100000000000010000000101111 ],
    [ "sc.w.rl        rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011010000000000010000000101111 ],
    [ "sc.w.aqrl      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011110000000000010000000101111 ],
    [ "amoswap.w      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001000000000000010000000101111 ],
    [ "amoswap.w.aq   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001100000000000010000000101111 ],
    [ "amoswap.w.rl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001010000000000010000000101111 ],
    [ "amoswap.w.aqrl rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001110000000000010000000101111 ],
    [ "amoadd.w       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000000000000000010000000101111 ],
    [ "amoadd.w.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000100000000000010000000101111 ],
    [ "amoadd.w.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000010000000000010000000101111 ],
    [ "amoadd.w.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000110000000000010000000101111 ],
    [ "amoxor.w       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100000000000000010000000101111 ],
    [ "amoxor.w.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100100000000000010000000101111 ],
    [ "amoxor.w.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100010000000000010000000101111 ],
    [ "amoxor.w.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100110000000000010000000101111 ],
    [ "amoand.w       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100000000000000010000000101111 ],
    [ "amoand.w.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100100000000000010000000101111 ],
    [ "amoand.w.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100010000000000010000000101111 ],
    [ "amoand.w.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100110000000000010000000101111 ],
    [ "amoor.w        rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000000000000000010000000101111 ],
    [ "amoor.w.aq     rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000100000000000010000000101111 ],
    [ "amoor.w.rl     rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000010000000000010000000101111 ],
    [ "amoor.w.aqrl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000110000000000010000000101111 ],
    [ "amomin.w       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000000000000000010000000101111 ],
    [ "amomin.w.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000100000000000010000000101111 ],
    [ "amomin.w.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000010000000000010000000101111 ],
    [ "amomin.w.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000110000000000010000000101111 ],
    [ "amomax.w       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100000000000000010000000101111 ],
    [ "amomax.w.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100100000000000010000000101111 ],
    [ "amomax.w.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100010000000000010000000101111 ],
    [ "amomax.w.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100110000000000010000000101111 ],
    [ "amominu.w      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000000000000000010000000101111 ],
    [ "amominu.w.aq   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000100000000000010000000101111 ],
    [ "amominu.w.rl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000010000000000010000000101111 ],
    [ "amominu.w.aqrl rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000110000000000010000000101111 ],
    [ "amomaxu.w      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100000000000000010000000101111 ],
    [ "amomaxu.w.aq   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100100000000000010000000101111 ],
    [ "amomaxu.w.rl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100010000000000010000000101111 ],
    [ "amomaxu.w.aqrl rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100110000000000010000000101111 ],

    [ "lr.d           rd, rs1",           0b11111111111100000111000001111111, 0b00010000000000000011000000101111 ],
    [ "lr.d.aq        rd, rs1",           0b11111111111100000111000001111111, 0b00010100000000000011000000101111 ],
    [ "lr.d.rl        rd, rs1",           0b11111111111100000111000001111111, 0b00010010000000000011000000101111 ],
    [ "lr.d.aqrl      rd, rs1",           0b11111111111100000111000001111111, 0b00010110000000000011000000101111 ],
    [ "sc.d           rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011000000000000011000000101111 ],
    [ "sc.d.aq        rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011100000000000011000000101111 ],
    [ "sc.d.rl        rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011010000000000011000000101111 ],
    [ "sc.d.aqrl      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00011110000000000011000000101111 ],
    [ "amoswap.d      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001000000000000011000000101111 ],
    [ "amoswap.d.aq   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001100000000000011000000101111 ],
    [ "amoswap.d.rl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001010000000000011000000101111 ],
    [ "amoswap.d.aqrl rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00001110000000000011000000101111 ],
    [ "amoadd.d       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000000000000000011000000101111 ],
    [ "amoadd.d.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000100000000000011000000101111 ],
    [ "amoadd.d.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000010000000000011000000101111 ],
    [ "amoadd.d.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00000110000000000011000000101111 ],
    [ "amoxor.d       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100000000000000011000000101111 ],
    [ "amoxor.d.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100100000000000011000000101111 ],
    [ "amoxor.d.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100010000000000011000000101111 ],
    [ "amoxor.d.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b00100110000000000011000000101111 ],
    [ "amoand.d       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100000000000000011000000101111 ],
    [ "amoand.d.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100100000000000011000000101111 ],
    [ "amoand.d.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100010000000000011000000101111 ],
    [ "amoand.d.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01100110000000000011000000101111 ],
    [ "amoor.d        rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000000000000000011000000101111 ],
    [ "amoor.d.aq     rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000100000000000011000000101111 ],
    [ "amoor.d.rl     rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000010000000000011000000101111 ],
    [ "amoor.d.aqrl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b01000110000000000011000000101111 ],
    [ "amomin.d       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000000000000000011000000101111 ],
    [ "amomin.d.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000100000000000011000000101111 ],
    [ "amomin.d.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000010000000000011000000101111 ],
    [ "amomin.d.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10000110000000000011000000101111 ],
    [ "amomax.d       rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100000000000000011000000101111 ],
    [ "amomax.d.aq    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100100000000000011000000101111 ],
    [ "amomax.d.rl    rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100010000000000011000000101111 ],
    [ "amomax.d.aqrl  rd, rs1, rs2",      0b11111110000000000111000001111111, 0b10100110000000000011000000101111 ],
    [ "amominu.d      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000000000000000011000000101111 ],
    [ "amominu.d.aq   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000100000000000011000000101111 ],
    [ "amominu.d.rl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000010000000000011000000101111 ],
    [ "amominu.d.aqrl rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11000110000000000011000000101111 ],
    [ "amomaxu.d      rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100000000000000011000000101111 ],
    [ "amomaxu.d.aq   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100100000000000011000000101111 ],
    [ "amomaxu.d.rl   rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100010000000000011000000101111 ],
    [ "amomaxu.d.aqrl rd, rs1, rs2",      0b11111110000000000111000001111111, 0b11100110000000000011000000101111 ],

    #-----------------------------------------------------------------------
    # Illegal Instruction
    #-----------------------------------------------------------------------
    [ "invld",                       0b11111111111111111111111111111111, 0b00000000110000001111111111101110 ], # 0x0c00ffee
]

#=========================================================================
# Field Definitions
#=========================================================================
# For each field tag used in the above instruction templates, we need to
# define: (1) a slice object specifying where the field is encoded in the
# instruction; (2) an assembly_field function that takes the instruction
# bits instruction and a string for the field as input and assembles the
# field string into the appropriate bits of the instruction; and (3) a
# disassembly_field function that takes the instruction bits as input,
# extracts the appropriate field, and converts it into a string.

#-------------------------------------------------------------------------
# Define slice for each field
#-------------------------------------------------------------------------

# See "The RISC-V Instruction Set Manual Volume I User-Level ISA.pdf" pp.23
# "Base Instruction Formats" and "Immediate Encoding Variants"

#  31          25 24   20 19   15 14    12 11          7 6      0
# | funct7       | rs2   | rs1   | funct3 | rd          | opcode |  R-type
# | imm[11:0]            | rs1   | funct3 | rd          | opcode |  I-type, I-imm
# | imm[11:5]    | rs2   | rs1   | funct3 | imm[4:0]    | opcode |  S-type, S-imm
# | imm[12|10:5] | rs2   | rs1   | funct3 | imm[4:1|11] | opcode |  SB-type,B-imm
# | imm[31:12]                            | rd          | opcode |  U-type, U-imm
# | imm[20|10:1|11|19:12]                 | rd          | opcode |  UJ-type,J-imm

# Note python slice [ a, b ) == above slice [ b-1, a ]

tinyrv2_field_slice_opcode = slice( 0, 7 )
tinyrv2_field_slice_funct2 = slice( 25, 27 )
tinyrv2_field_slice_funct3 = slice( 12, 15 )
tinyrv2_field_slice_funct7 = slice( 25, 32 )

tinyrv2_field_slice_rd = slice( 7, 12 )
tinyrv2_field_slice_rs1 = slice( 15, 20 )
tinyrv2_field_slice_rs2 = slice( 20, 25 )
tinyrv2_field_slice_shamt = slice( 20, 25 )

tinyrv2_field_slice_i_imm = slice( 20, 32 )
tinyrv2_field_slice_csrnum = slice( 20, 32 )

tinyrv2_field_slice_s_imm0 = slice( 7, 12 )
tinyrv2_field_slice_s_imm1 = slice( 25, 32 )

tinyrv2_field_slice_b_imm0 = slice( 8, 12 )
tinyrv2_field_slice_b_imm1 = slice( 25, 31 )
tinyrv2_field_slice_b_imm2 = slice( 7, 8 )
tinyrv2_field_slice_b_imm3 = slice( 31, 32 )

tinyrv2_field_slice_u_imm = slice( 12, 32 )

tinyrv2_field_slice_j_imm0 = slice( 21, 31 )
tinyrv2_field_slice_j_imm1 = slice( 20, 21 )
tinyrv2_field_slice_j_imm2 = slice( 12, 20 )
tinyrv2_field_slice_j_imm3 = slice( 31, 32 )

tinyrv2_field_slice_c_imm = tinyrv2_field_slice_rs1

tinyrv2_field_slice_pred = slice( 24, 28 )
tinyrv2_field_slice_succ = slice( 20, 24 )

tinyrv2_field_slice_aq = slice( 26, 27 )
tinyrv2_field_slice_rl = slice( 25, 26 )

#-------------------------------------------------------------------------
# rs1 assembly/disassembly functions
#-------------------------------------------------------------------------

# See "The RISC-V Instruction Set Manual Volume I User-Level ISA.pdf" pp.21
# "Programmers" Model for Base Integer Subset" for register specifiers
# x0 .. x31


def assemble_field_rs1( bits, sym, pc, field_str ):

  # Register specifiers must begin with an "x"
  assert field_str[ 0 ] == "x"

  # Register specifier must be between 0 and 31
  reg_specifier = int( field_str.lstrip( "x" ) )
  assert 0 <= reg_specifier <= 31

  bits[ tinyrv2_field_slice_rs1 ] = reg_specifier


def disassemble_field_rs1( bits ):
  return "x{:0>2}".format( bits[ tinyrv2_field_slice_rs1 ].uint() )


#-------------------------------------------------------------------------
# rs2 assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_rs2( bits, sym, pc, field_str ):

  # Register specifiers must begin with an "x"
  assert field_str[ 0 ] == "x"

  # Register specifier must be between 0 and 31
  reg_specifier = int( field_str.lstrip( "x" ) )
  assert 0 <= reg_specifier <= 31

  bits[ tinyrv2_field_slice_rs2 ] = reg_specifier


def disassemble_field_rs2( bits ):
  return "x{:0>2}".format( bits[ tinyrv2_field_slice_rs2 ].uint() )


#-------------------------------------------------------------------------
# shamt assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_shamt( bits, sym, pc, field_str ):

  shamt = int( field_str, 0 )
  assert 0 <= shamt <= 31

  bits[ tinyrv2_field_slice_shamt ] = shamt


def disassemble_field_shamt( bits ):
  return "{:0>2x}".format( bits[ tinyrv2_field_slice_shamt ].uint() )


#-------------------------------------------------------------------------
# rd assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_rd( bits, sym, pc, field_str ):

  # Register specifiers must begin with an "x"
  assert field_str[ 0 ] == "x"

  # Register specifier must be between 0 and 31
  reg_specifier = int( field_str.lstrip( "x" ) )
  assert 0 <= reg_specifier <= 31

  bits[ tinyrv2_field_slice_rd ] = reg_specifier


def disassemble_field_rd( bits ):
  return "x{:0>2}".format( bits[ tinyrv2_field_slice_rd ].uint() )


#-------------------------------------------------------------------------
# i_imm assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_i_imm( bits, sym, pc, field_str ):

  # Check to see if the immediate field derives from a label
  if field_str[ 0 ] == "%":
    label_addr = Bits( 32, sym[ field_str[ 4:-1 ] ] )
    if field_str.startswith( "%hi[" ):
      imm = label_addr[ 20:32 ]
    elif field_str.startswith( "%md[" ):
      imm = label_addr[ 13:25 ]
    elif field_str.startswith( "%lo[" ):
      imm = label_addr[ 0:12 ]
  else:
    imm = int( field_str, 0 )

  assert imm < ( 1 << 12 )

  bits[ tinyrv2_field_slice_i_imm ] = imm


def disassemble_field_i_imm( bits ):
  return "0x{:0>3x}".format( bits[ tinyrv2_field_slice_i_imm ].uint() )


def assemble_field_csrnum( bits, sym, pc, field_str ):

  imm = CsrRegisters.lookup( field_str )
  bits[ tinyrv2_field_slice_csrnum ] = imm


def disassemble_field_csrnum( bits ):
  return "0x{:0>3x}".format( bits[ tinyrv2_field_slice_csrnum ].uint() )


#-------------------------------------------------------------------------
# s_imm assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_s_imm( bits, sym, pc, field_str ):

  imm = Bits( 12, int( field_str, 0 ) )

  bits[ tinyrv2_field_slice_s_imm0 ] = imm[ 0:5 ]
  bits[ tinyrv2_field_slice_s_imm1 ] = imm[ 5:12 ]


def disassemble_field_s_imm( bits ):
  imm = Bits( 12, 0 )
  imm[ 0:5 ] = bits[ tinyrv2_field_slice_s_imm0 ]
  imm[ 5:12 ] = bits[ tinyrv2_field_slice_s_imm1 ]

  return "0x{:0>3x}".format( imm.uint() )


#-------------------------------------------------------------------------
# b_imm assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_b_imm( bits, sym, pc, field_str ):

  if sym.has_key( field_str ):
    # notice that we encode the branch target address (a lable) relative
    # to current PC
    btarg_byte_addr = sym[ field_str ] - pc
  else:
    btarg_byte_addr = int( field_str, 0 )

  imm = Bits( 13, btarg_byte_addr )

  bits[ tinyrv2_field_slice_b_imm0 ] = imm[ 1:5 ]
  bits[ tinyrv2_field_slice_b_imm1 ] = imm[ 5:11 ]
  bits[ tinyrv2_field_slice_b_imm2 ] = imm[ 11:12 ]
  bits[ tinyrv2_field_slice_b_imm3 ] = imm[ 12:13 ]


def disassemble_field_b_imm( bits ):

  imm = Bits( 13, 0 )
  imm[ 1:5 ] = bits[ tinyrv2_field_slice_b_imm0 ]
  imm[ 5:11 ] = bits[ tinyrv2_field_slice_b_imm1 ]
  imm[ 11:12 ] = bits[ tinyrv2_field_slice_b_imm2 ]
  imm[ 12:13 ] = bits[ tinyrv2_field_slice_b_imm3 ]

  return "0x{:0>4x}".format( imm.uint() )


#-------------------------------------------------------------------------
# u_imm assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_u_imm( bits, sym, pc, field_str ):

  # Check to see if the immediate field derives from a label
  if field_str[ 0 ] == "%":
    label_addr = Bits( 32, sym[ field_str[ 4:-1 ] ] )
    if field_str.startswith( "%hi[" ):
      imm = label_addr[ 12:32 ]
    elif field_str.startswith( "%lo[" ):
      imm = label_addr[ 0:12 ]
    else:
      assert False
  else:
    imm = int( field_str, 0 )

  assert imm < ( 1 << 20 )
  bits[ tinyrv2_field_slice_u_imm ] = imm


def disassemble_field_u_imm( bits ):
  return "0x{:0>5x}".format( bits[ tinyrv2_field_slice_u_imm ].uint() )


#-------------------------------------------------------------------------
# j_imm assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_j_imm( bits, sym, pc, field_str ):

  if sym.has_key( field_str ):
    # notice that we encode the branch target address (a lable) relative
    # to current PC
    jtarg_byte_addr = sym[ field_str ] - pc
  else:
    jtarg_byte_addr = int( field_str, 0 )

  imm = Bits( 21, jtarg_byte_addr )

  bits[ tinyrv2_field_slice_j_imm0 ] = imm[ 1:11 ]
  bits[ tinyrv2_field_slice_j_imm1 ] = imm[ 11:12 ]
  bits[ tinyrv2_field_slice_j_imm2 ] = imm[ 12:20 ]
  bits[ tinyrv2_field_slice_j_imm3 ] = imm[ 20:21 ]


def disassemble_field_j_imm( bits ):
  imm = Bits( 21, 0 )
  imm[ 1:11 ] = bits[ tinyrv2_field_slice_j_imm0 ]
  imm[ 11:12 ] = bits[ tinyrv2_field_slice_j_imm1 ]
  imm[ 12:20 ] = bits[ tinyrv2_field_slice_j_imm2 ]
  imm[ 20:21 ] = bits[ tinyrv2_field_slice_j_imm3 ]
  return "0x{:0>6x}".format( imm.uint() )


#-------------------------------------------------------------------------
# c_imm assembly/disassembly functions
#-------------------------------------------------------------------------


def assemble_field_c_imm( bits, sym, pc, field_str ):
  imm = Bits( 5, int( field_str, 0 ) )

  bits[ tinyrv2_field_slice_c_imm ] = imm


def disassemble_field_c_imm( bits ):
  imm = bits[ tinyrv2_field_slice_c_imm ]
  return "0x{:0>2x}".format( imm.uint() )


fence_spec = 'iorw'
fence_locs = dict([( c, i ) for c, i in enumerate( fence_spec ) ] )


def parse_fence_spec( spec ):
  assert len( spec ) < len( fence_locs )
  result = Bits( len( fence_locs ), 0 )
  for c in spec:
    assert c in fence_locs
    assert not result[ fence_locs[ c ] ]
    result[ fence_locs[ c ] ] = 1

  return result


def format_fence_spec( value ):
  result = ''
  for c in fence_spec:
    if value[ fence_locs[ c ] ]:
      result += c
  return result


def assemble_field_pred( bits, sym, pc, field_str ):
  bits[ tinyrv2_field_slize_pred ] = parse_fence_spec( field_str )


def disassemble_field_pred( bits ):
  return format_fence_spec( bits[ tinyrv2_field_slize_pred ] )


def assemble_field_succ( bits, sym, pc, field_str ):
  bits[ tinyrv2_field_slize_succ ] = parse_fence_spec( field_str )


def disassemble_field_succ( bits ):
  return format_fence_spec( bits[ tinyrv2_field_slize_succ ] )


#-------------------------------------------------------------------------
# Field Dictionary
#-------------------------------------------------------------------------
# Create a dictionary so we can lookup an assemble field function
# based on the field tag. I imagine we can eventually use some kind of
# Python magic to eliminate this boiler plate code.

tinyrv2_fields = \
{
    "rs1"    : [ assemble_field_rs1,    disassemble_field_rs1    ],
    "rs2"    : [ assemble_field_rs2,    disassemble_field_rs2    ],
    "shamt"  : [ assemble_field_shamt,  disassemble_field_shamt  ],
    "rd"     : [ assemble_field_rd,     disassemble_field_rd     ],
    "i_imm"  : [ assemble_field_i_imm,  disassemble_field_i_imm  ],
    "csrnum" : [ assemble_field_csrnum, disassemble_field_csrnum ],
    "s_imm"  : [ assemble_field_s_imm,  disassemble_field_s_imm  ],
    "b_imm"  : [ assemble_field_b_imm,  disassemble_field_b_imm  ],
    "u_imm"  : [ assemble_field_u_imm,  disassemble_field_u_imm  ],
    "j_imm"  : [ assemble_field_j_imm,  disassemble_field_j_imm  ],
    "c_imm"  : [ assemble_field_c_imm,  disassemble_field_c_imm  ],
    "pred"   : [ assemble_field_pred,   disassemble_field_pred   ],
    "succ"   : [ assemble_field_succ,   disassemble_field_succ   ],
}

#=========================================================================
# IsaImpl
#=========================================================================
# We use the encoding table and assembly/disassembly field functions to
# instantiate an IsaImpl objection which we can then use in our
# assembly/disassembly functions. I am not sure if we still want to
# refactor this here, but it is good enough for now.


class IsaImpl( object ):

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self, nbits, inst_encoding_table, inst_fields ):

    self.nbits = nbits
    self.inst_encoding_table = inst_encoding_table
    self.asm_field_funcs_dict = {}
    self.disasm_field_funcs_dict = {}
    self.opcode_match_dict = {}

    self.disasm_field_funcs_dict[ '' ] = {}  # this is for all-zero case

    for row in inst_encoding_table:

      # Extract the columns from the row

      inst_tmpl = row[ 0 ]
      opcode_mask = row[ 1 ]
      opcode_match = row[ 2 ]

      # Extract instruction name from string template

      ( inst_name, sep, inst_tmpl ) = inst_tmpl.partition( ' ' )

      # Add opcode match to the a dictionary using the instruction
      # name as the key

      self.opcode_match_dict[ inst_name ] = opcode_match

      # Split the remainder of the template into field strings. First we
      # translate non-whitespace deliminters into whitespace so that we
      # can use split.

      translation_table = maketrans( ",()", "   " )
      inst_field_tags = translate( inst_tmpl, translation_table ).split()

      # Create the list of asm field functions

      asm_field_funcs = []
      for asm_field_tag in inst_field_tags:
        asm_field_funcs.append( inst_fields[ asm_field_tag ][ 0 ] )

      # Add the list of asm field functions to the encoding

      self.asm_field_funcs_dict[ inst_name ] = asm_field_funcs

      # Create the list of disasm field functions

      disasm_field_funcs = {}
      for asm_field_tag in inst_field_tags:
        disasm_field_funcs[ asm_field_tag ] = inst_fields[ asm_field_tag ][ 1 ]

      # Add the list of disasm field functions to the encoding

      self.disasm_field_funcs_dict[ inst_name ] = disasm_field_funcs

  #-----------------------------------------------------------------------
  # decode_tmpl
  #-----------------------------------------------------------------------
  # For now this is O(n) where n is the number of instructions in the
  # encoding table. Obviously, this is pretty slow. I am sure we can do
  # better by creating some kind of tree-based data structure.

  def decode_tmpl( self, inst_bits ):

    if inst_bits == 0:  # hacky
      return ""

    for row in self.inst_encoding_table:

      # Extract the columns from the row

      inst_tmpl = row[ 0 ]
      opcode_mask = row[ 1 ]
      opcode_match = row[ 2 ]

      # If match, then return instruction name

      if ( inst_bits & opcode_mask ) == opcode_match:
        return inst_tmpl

    # Illegal instruction

    raise AssertionError( "Illegal instruction {}!".format( inst_bits ) )

  #-----------------------------------------------------------------------
  # decode_name
  #-----------------------------------------------------------------------

  def decode_inst_name( self, inst_bits ):

    # Decode template

    inst_tmpl = self.decode_tmpl( inst_bits )

    # Extract instruction name

    return inst_tmpl.partition( ' ' )[ 0 ]

  #-----------------------------------------------------------------------
  # assemble_inst
  #-----------------------------------------------------------------------

  def assemble_inst( self, sym, pc, inst_str ):

    # Extract instruction name from asm string

    ( inst_name, sep, inst_str ) = inst_str.partition( ' ' )

    # Use the instruction name to get the opcode match which we can
    # the use to initialize the instruction bits

    inst_bits = Bits( self.nbits, self.opcode_match_dict[ inst_name ] )

    # Split the remainder of the asm string into field strings. First
    # we translate non-whitespace deliminters into whitespace so that
    # we can use split.

    translation_table = maketrans( ",()", "   " )
    asm_field_strs = translate( inst_str, translation_table ).split()

    # Retrieve the list of asm field functions for this instruction

    asm_field_funcs = self.asm_field_funcs_dict[ inst_name ]

    # Apply these asm field functions to the asm field strings

    for asm_field_str, asm_field_func in zip( asm_field_strs, asm_field_funcs ):
      asm_field_func( inst_bits, sym, pc, asm_field_str )

    # Return the assembled instruction

    return inst_bits

  #-----------------------------------------------------------------------
  # disassemble_inst
  #-----------------------------------------------------------------------

  def disassemble_inst( self, inst_bits ):

    # Decode the instruction to find instruction template

    inst_tmpl = self.decode_tmpl( inst_bits )

    # Extract instruction name from asm template

    inst_name = inst_tmpl.partition( ' ' )[ 0 ]

    # Retrieve the list of disasm field functions for this instruction

    disasm_field_funcs = self.disasm_field_funcs_dict[ inst_name ]

    # Apply these asm field functions to create the disasm string

    inst_str = inst_tmpl
    for inst_field_tag, disasm_field_func in disasm_field_funcs.iteritems():
      field_str = disasm_field_func( inst_bits )
      inst_str = inst_str.replace( inst_field_tag, field_str )

    # Return the disassembled instruction

    return inst_str


# Here is the actual riscv_isa_impl. I think I refactored this because the
# idea was that the IsaImpl class could be reused across different ISAs?

tinyrv2_isa_impl = IsaImpl( 32, tinyrv2_encoding_table, tinyrv2_fields )

#=========================================================================
# Assemble
#=========================================================================

# https://docs.python.org/2/library/struct.html#format-characters
# 64 bit data elements packed as unsigned long long
if XLEN == 64:
  DATA_PACK_DIRECTIVE = "<Q"
else:
  DATA_PACK_DIRECTIVE = "<I"


def assemble_inst( sym, pc, inst_str ):
  return tinyrv2_isa_impl.assemble_inst( sym, pc, inst_str )


def assemble( asm_code ):
  # If asm_code is a single string, then put it in a list to simplify the
  # rest of the logic.

  asm_code_list = asm_code
  if isinstance( asm_code, str ):
    asm_code_list = [ asm_code ]

  # Create a single list of lines

  asm_list = []
  for asm_seq in asm_code_list:
    asm_list.extend( asm_seq.splitlines() )

  # First pass to create symbol table. This is obviously very simplistic.
  # We can maybe make it more robust in the future.

  addr = int( RESET_VECTOR )
  sym = {}
  for line in asm_list:
    line = line.partition( '#' )[ 0 ]
    line = line.strip()

    if line == "":
      continue

    if line.startswith( ".offset" ):
      ( cmd, sep, addr_str ) = line.partition( ' ' )
      addr = int( addr_str, 0 )

    elif line.startswith( ".data" ):
      pass

    else:
      ( label, sep, rest ) = line.partition( ':' )
      if sep != "":
        sym[ label.strip() ] = addr
      else:
        addr += ILEN_BYTES

  # Second pass to assemble text section

  asm_list_idx = 0
  addr = int( RESET_VECTOR )
  text_bytes = bytearray()
  mngr2proc_bytes = bytearray()
  proc2mngr_bytes = bytearray()

  # Shunning: the way I handle multiple manager is as follows.
  #
  # At the beginning the single_core sign is true and all "> 1" "< 2"
  # values are dumped into the above mngr2proc_bytes and mngr2proc_bytes.
  # So, for single core testing the assembler works as usual.
  #
  # For multicore testing, I assume that all lists wrapped by curly braces
  # have the same width, and I will use the first ever length as the number
  # of cores. For example, when I see "> {1,2,3,4}", it means there are 4
  # cores. It will then set single_core=False and num_cores=4.
  # Later if I see "> {1,2,3}" I will throw out assertion error.
  #
  # Also, Upon the first occurence of the mentioned curly braces, I will
  # just duplicate mngr2proc_bytes for #core times, and put the duplicates
  # into mngrs2procs.  Later, when I see a "> 1", I will check the
  # single_core flag. If it's False, it will dump the check message into
  # all the duplicated bytearrays.
  #
  # The problem of co-existence if we keep mngr2proc and mngrs2procs, is
  # that unless we record the exact order we receive the csr instructions,
  # we cannot arbitrarily interleave the values in mngr2proc and mngrs2procs.

  mngrs2procs_bytes = []
  procs2mngrs_bytes = []
  single_core = True
  num_cores = 1

  def duplicate():

    # duplicate the bytes and no more mngr2proc/proc2mngr

    for i in xrange( num_cores ):
      mngrs2procs_bytes.append( bytearray() )
      mngrs2procs_bytes[ i ][: ] = mngr2proc_bytes

      procs2mngrs_bytes.append( bytearray() )
      procs2mngrs_bytes[ i ][: ] = proc2mngr_bytes

  for line in asm_list:
    asm_list_idx += 1
    line = line.partition( '#' )[ 0 ]
    line = line.strip()

    if line == "":
      continue

    if line.startswith( ".offset" ):
      ( cmd, sep, addr_str ) = line.partition( ' ' )
      addr = int( addr_str, 0 )

    elif line.startswith( ".data" ):
      break

    else:
      if ':' not in line:

        inst_str = line

        # First see if we have either a < or a >

        if '<' in line:
          ( temp, sep, value ) = line.partition( '<' )

          value = value.lstrip( ' ' )
          if value.startswith( '{' ):
            values = map( lambda x: int( x, 0 ), value[ 1:-1 ].split( ',' ) )

            if not single_core and len( values ) != num_cores:
              raise Exception(
                  "Previous curly brace pair has {} elements in between, but this one \"{}\" has {}."
                  .format( num_cores, line, len( values ) ) )

            if single_core:
              single_core = False
              num_cores = len( values )
              duplicate()

            for i in xrange( num_cores ):
              mngrs2procs_bytes[ i ].extend(
                  struct.pack( DATA_PACK_DIRECTIVE, Bits( XLEN,
                                                          values[ i ] ) ) )

          else:
            bits = Bits( XLEN, int( value, 0 ) )

            if single_core:
              mngr2proc_bytes.extend( struct.pack( DATA_PACK_DIRECTIVE, bits ) )
            else:
              for x in mngrs2procs_bytes:
                x.extend( struct.pack( DATA_PACK_DIRECTIVE, bits ) )

          inst_str = temp

        elif '>' in line:
          ( temp, sep, value ) = line.partition( '>' )

          value = value.lstrip( ' ' )
          if value.startswith( '{' ):
            values = map( lambda x: int( x, 0 ), value[ 1:-1 ].split( ',' ) )

            if not single_core and len( values ) != num_cores:
              raise Exception(
                  "Previous curly brace pair has {} elements in between, but this one \"{}\" has {}."
                  .format( num_cores, line, len( values ) ) )

            if single_core:
              single_core = False
              num_cores = len( values )
              duplicate()

            for i in xrange( num_cores ):
              procs2mngrs_bytes[ i ].extend(
                  struct.pack( DATA_PACK_DIRECTIVE, Bits( XLEN,
                                                          values[ i ] ) ) )

          else:
            bits = Bits( XLEN, int( value, 0 ) )

            if single_core:
              proc2mngr_bytes.extend( struct.pack( DATA_PACK_DIRECTIVE, bits ) )
            else:
              for x in procs2mngrs_bytes:
                x.extend( struct.pack( DATA_PACK_DIRECTIVE, bits ) )

          inst_str = temp

        bits = assemble_inst( sym, addr, inst_str )
        text_bytes.extend( struct.pack( "<I", bits.uint() ) )
        addr += 4

  # Assemble data section

  data_bytes = bytearray()
  for line in asm_list[ asm_list_idx:]:
    line = line.partition( '#' )[ 0 ]
    line = line.strip()

    if line == "":
      continue

    if line.startswith( ".offset" ):
      ( cmd, sep, addr_str ) = line.partition( ' ' )
      addr = int( addr_str, 0 )

    elif line.startswith( ".word" ):
      ( cmd, sep, value ) = line.partition( ' ' )
      data_bytes.extend( struct.pack( "<I", int( value, 0 ) ) )
      addr += 4

    elif line.startswith( ".hword" ):
      ( cmd, sep, value ) = line.partition( ' ' )
      data_bytes.extend( struct.pack( "<H", int( value, 0 ) ) )
      addr += 2

    elif line.startswith( ".byte" ):
      ( cmd, sep, value ) = line.partition( ' ' )
      data_bytes.extend( struct.pack( "<B", int( value, 0 ) ) )
      addr += 1

  # Construct the corresponding section objects

  text_section = \
    SparseMemoryImage.Section( ".text", 0x0200, text_bytes )

  data_section = SparseMemoryImage.Section( ".data", 0x2000, data_bytes )

  # Build a sparse memory image

  mem_image = SparseMemoryImage()
  mem_image.add_section( text_section )

  if len( data_section.data ) > 0:
    mem_image.add_section( data_section )

  if single_core:

    mngr2proc_section = \
      SparseMemoryImage.Section( ".mngr2proc", 0x13000, mngr2proc_bytes )

    if len( mngr2proc_section.data ) > 0:
      mem_image.add_section( mngr2proc_section )

    proc2mngr_section = \
      SparseMemoryImage.Section( ".proc2mngr", 0x14000, proc2mngr_bytes )

    if len( proc2mngr_section.data ) > 0:
      mem_image.add_section( proc2mngr_section )

  else:

    for i in xrange( len( mngrs2procs_bytes ) ):
      img = SparseMemoryImage.Section( ".mngr{}_2proc".format( i ),
                                       0x15000 + 0x1000 * i,
                                       mngrs2procs_bytes[ i ] )

      if len( img.data ) > 0:
        mem_image.add_section( img )

    for i in xrange( len( procs2mngrs_bytes ) ):
      img = SparseMemoryImage.Section( ".proc{}_2mngr".format( i ),
                                       0x16000 + 0x2000 * i,
                                       procs2mngrs_bytes[ i ] )
      if len( img.data ) > 0:
        mem_image.add_section( img )

  return mem_image


#=========================================================================
# Disassemble
#=========================================================================


def disassemble_inst( inst_bits ):
  return tinyrv2_isa_impl.disassemble_inst( inst_bits )


def decode_inst_name( inst ):

  # Originally I was just using this:
  #
  #  return parc_isa_impl.decode_inst_name( inst_bits )
  #
  # which basically just does a linear search in the encoding table to
  # find a match. Eventually, I think we should figure out a way to
  # automatically turn the encoding table into some kind of fast
  # tree-bsaed search, but for now we just explicitly create a big case
  # statement to do the instruction name decode.

  # Short names

  opcode = tinyrv2_field_slice_opcode
  funct3 = tinyrv2_field_slice_funct3
  funct7 = tinyrv2_field_slice_funct7

  inst_name = ""

  if inst[ opcode ] == 0b0110011:
    if inst[ funct7 ] == 0b0000000:
      if inst[ funct3 ] == 0b000:
        inst_name = "add"
      elif inst[ funct3 ] == 0b001:
        inst_name = "sll"
      elif inst[ funct3 ] == 0b010:
        inst_name = "slt"
      elif inst[ funct3 ] == 0b011:
        inst_name = "sltu"
      elif inst[ funct3 ] == 0b100:
        inst_name = "xor"
      elif inst[ funct3 ] == 0b101:
        inst_name = "srl"
      elif inst[ funct3 ] == 0b110:
        inst_name = "or"
      elif inst[ funct3 ] == 0b111:
        inst_name = "and"
    elif inst[ funct7 ] == 0b0100000:
      if inst[ funct3 ] == 0b000:
        inst_name = "sub"
      elif inst[ funct3 ] == 0b101:
        inst_name = "sra"
    elif inst[ funct7 ] == 0b0000001:
      if inst[ funct3 ] == 0b000:
        inst_name = "mul"

  elif inst[ opcode ] == 0b0010011:
    if inst[ funct3 ] == 0b000:
      inst_name = "addi"
    elif inst[ funct3 ] == 0b010:
      inst_name = "slti"
    elif inst[ funct3 ] == 0b011:
      inst_name = "sltiu"
    elif inst[ funct3 ] == 0b100:
      inst_name = "xori"
    elif inst[ funct3 ] == 0b110:
      inst_name = "ori"
    elif inst[ funct3 ] == 0b111:
      inst_name = "andi"
    elif inst[ funct3 ] == 0b001:
      inst_name = "slli"
    elif inst[ funct3 ] == 0b101:
      if inst[ funct7 ] == 0b0000000:
        inst_name = "srli"
      elif inst[ funct7 ] == 0b0100000:
        inst_name = "srai"

  elif inst[ opcode ] == 0b0100011:
    if inst[ funct3 ] == 0b011:
      inst_name = "sw"
    elif inst[ funct3 ] == 0b010:
      inst_name = "sw"
    elif inst[ funct3 ] == 0b000:
      inst_name = "sb"

  elif inst[ opcode ] == 0b0000011:
    if inst[ funct3 ] == 0b000:
      inst_name = "lb"
    elif inst[ funct3 ] == 0b001:
      inst_name = "lh"
    elif inst[ funct3 ] == 0b010:
      inst_name = "lw"
    elif inst[ funct3 ] == 0b011:
      inst_name = "ld"
    elif inst[ funct3 ] == 0b100:
      inst_name = "lbu"
    elif inst[ funct3 ] == 0b101:
      inst_name = "lhu"
    elif inst[ funct3 ] == 0b110:
      inst_name = "lwu"

  elif inst[ opcode ] == 0b1100011:
    if inst[ funct3 ] == 0b000:
      inst_name = "beq"
    elif inst[ funct3 ] == 0b001:
      inst_name = "bne"
    elif inst[ funct3 ] == 0b100:
      inst_name = "blt"
    elif inst[ funct3 ] == 0b101:
      inst_name = "bge"
    elif inst[ funct3 ] == 0b110:
      inst_name = "bltu"
    elif inst[ funct3 ] == 0b111:
      inst_name = "bgeu"

  elif inst[ opcode ] == 0b0110111:
    inst_name = "lui"

  elif inst[ opcode ] == 0b0010111:
    inst_name = "auipc"

  elif inst[ opcode ] == 0b1101111:
    inst_name = "jal"

  elif inst[ opcode ] == 0b1100111:
    inst_name = "jalr"

  elif inst[ opcode ] == 0b1110011:
    if inst[ funct3 ] == 0b001:
      inst_name = "csrrw"
    elif inst[ funct3 ] == 0b010:
      inst_name = "csrrs"
    elif inst[ funct3 ] == 0b011:
      inst_name = "csrrc"
    elif inst[ funct3 ] == 0b101:
      inst_name = "csrrwi"
    elif inst[ funct3 ] == 0b110:
      inst_name = "csrrsi"
    elif inst[ funct3 ] == 0b111:
      inst_name = "csrrci"

  if inst_name == "":
    return "invld"

  return inst_name


def disassemble( mem_image ):

  # Get the text section to disassemble

  text_section = mem_image.get_section( ".text" )

  # Iterate through the text section four bytes at a time

  addr = text_section.addr
  asm_code = ""
  for i in xrange( 0, len( text_section.data ), 4 ):

    print hex( addr + i )

    bits = struct.unpack_from( "<I", buffer( text_section.data, i, 4 ) )[ 0 ]
    inst_str = disassemble_inst( Bits( 32, bits ) )
    disasm_line = " {:0>8x}  {:0>8x}  {}\n".format( addr + i, bits, inst_str )
    asm_code += disasm_line

  return asm_code


#=========================================================================
# TinyRV2Inst
#=========================================================================
# This is a concrete instruction class for TinyRV2 with methods for
# accessing the various instruction fields.


class TinyRV2Inst( object ):

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self, inst_bits ):
    self.bits = Bits( ILEN, inst_bits )

  #-----------------------------------------------------------------------
  # Get instruction name
  #-----------------------------------------------------------------------

  @property
  def name( self ):
    return decode_inst_name( self.bits )

  #-----------------------------------------------------------------------
  # Get fields
  #-----------------------------------------------------------------------

  @property
  def rd( self ):
    return self.bits[ tinyrv2_field_slice_rd ]

  @property
  def rs1( self ):
    return self.bits[ tinyrv2_field_slice_rs1 ]

  @property
  def rs2( self ):
    return self.bits[ tinyrv2_field_slice_rs2 ]

  @property
  def shamt( self ):
    return self.bits[ tinyrv2_field_slice_shamt ]

  @property
  def i_imm( self ):
    return self.bits[ tinyrv2_field_slice_i_imm ]

  @property
  def s_imm( self ):
    imm = Bits( 12, 0 )
    imm[ 0:5 ] = self.bits[ tinyrv2_field_slice_s_imm0 ]
    imm[ 5:12 ] = self.bits[ tinyrv2_field_slice_s_imm1 ]
    return imm

  @property
  def b_imm( self ):
    imm = Bits( 13, 0 )
    imm[ 1:5 ] = self.bits[ tinyrv2_field_slice_b_imm0 ]
    imm[ 5:11 ] = self.bits[ tinyrv2_field_slice_b_imm1 ]
    imm[ 11:12 ] = self.bits[ tinyrv2_field_slice_b_imm2 ]
    imm[ 12:13 ] = self.bits[ tinyrv2_field_slice_b_imm3 ]
    return imm

  @property
  def u_imm( self ):
    return concat( self.bits[ tinyrv2_field_slice_u_imm ], Bits( 12, 0 ) )

  @property
  def j_imm( self ):
    imm = Bits( 21, 0 )
    imm[ 1:11 ] = self.bits[ tinyrv2_field_slice_j_imm0 ]
    imm[ 11:12 ] = self.bits[ tinyrv2_field_slice_j_imm1 ]
    imm[ 12:20 ] = self.bits[ tinyrv2_field_slice_j_imm2 ]
    imm[ 20:21 ] = self.bits[ tinyrv2_field_slice_j_imm3 ]
    return imm

  @property
  def c_imm( self ):
    imm = self.bits[ tinyrv2_field_slice_c_imm ]
    return imm

  @property
  def pred( self ):
    return self.bits[ tinyrv2_field_slice_pred ]

  @property
  def succ( self ):
    return self.bits[ tinyrv2_field_slice_succ ]

  @property
  def csrnum( self ):
    return self.bits[ tinyrv2_field_slice_i_imm ]

  @property
  def funct( self ):
    return self.bits[ tinyrv2_field_slice_funct7 ]

  #-----------------------------------------------------------------------
  # to string
  #-----------------------------------------------------------------------

  def __str__( self ):
    return disassemble_inst( self.bits )
