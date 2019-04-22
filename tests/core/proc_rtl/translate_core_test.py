from pymtl import *
from tests.context import lizard
from tests.config import test_verilog
from lizard.model.test_model import run_test_state_machine
from lizard.mem.rtl.memory_bus import MemMsg
from lizard.core.rtl.proc import Proc, ProcInterface
from lizard.model.translate import translate


def test_translate():
  translate(Proc(ProcInterface(), MemMsg(8, 2, 64, 8)))
