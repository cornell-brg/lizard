from pymtl import *
from tests.context import lizard
from lizard.util.rtl.alu import ALU, ALUInterface
from lizard.model.translate import translate


def test_translation():
  translate(ALU(ALUInterface(64)))
