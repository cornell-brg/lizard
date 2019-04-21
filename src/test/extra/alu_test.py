from pymtl import *
from util.rtl.alu import ALU, ALUInterface
from model.translate import translate


def test_translation():
  translate(ALU(ALUInterface(64)))
