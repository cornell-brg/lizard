from pymtl import *
from util.rtl.interface import UseInterface
from util.rtl.pipeline_stage import StageInterface, DropControllerInterface, DropControllerInterface, PipelineStageInterface, gen_stage
from util.rtl.register import Register, RegisterInterface
from model.wrapper import wrap_to_cl
from model.translate import translate
from model.hardware_model import NotReady, Result


class Counter(Model):

  def __init__(s):
    UseInterface(s, StageInterface(None, Bits(8)))

    s.counter = Register(RegisterInterface(Bits(8), enable=True), reset_value=0)
    s.connect(s.process_accepted, 1)
    s.connect(s.process_out, s.counter.read_data)
    s.connect(s.counter.write_call, s.process_call)

    @s.combinational
    def count():
      s.counter.write_data.v = s.counter.read_data + 1


class Add2(Model):

  def __init__(s):
    UseInterface(s, StageInterface(Bits(8), Bits(8)))

    s.connect(s.process_accepted, 1)

    @s.combinational
    def compute():
      s.process_out.v = s.process_in_ + 2


CounterStage = gen_stage(Counter)
Add2Stage = gen_stage(Add2)


class PipelinedCounter(Model):

  def __init__(s):
    UseInterface(s, PipelineStageInterface(Bits(8), None))

    s.stage_0 = CounterStage()
    s.stage_1 = Add2Stage()

    s.connect_m(s.stage_0.peek, s.stage_1.in_peek)
    s.connect_m(s.stage_0.take, s.stage_1.in_take)
    s.connect_m(s.stage_1.peek, s.peek)
    s.connect_m(s.stage_1.take, s.take)


def test_basic():
  rtl_dut = PipelinedCounter()
  rtl_dut.vcd_file = 'bob.vcd'
  dut = wrap_to_cl(translate(rtl_dut))
  # dut = wrap_to_cl(rtl_dut)

  dut.reset()
  assert isinstance(dut.peek(), NotReady)

  dut.cycle()
  assert dut.peek().msg == 2

  dut.cycle()
  assert dut.peek().msg == 2
  dut.take()

  dut.cycle()
  assert dut.peek().msg == 3
