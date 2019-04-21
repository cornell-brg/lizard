from pymtl import *
from test.config import test_verilog
from model.test_model import run_test_state_machine
from mem.rtl.memory_bus import MemMsg
from core.rtl.proc import Proc, ProcInterface
from model.translate import translate


def test_translate():
  translate(Proc(ProcInterface(), MemMsg(8, 2, 64, 8)))
