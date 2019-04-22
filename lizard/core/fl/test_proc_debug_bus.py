from pymtl import *
from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel
from collections import deque


class TestProcDebugBusFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, output_messages=[]):
    super(TestProcDebugBusFL, s).__init__(interface)

    s.state(
        output_messages=deque(output_messages),
        received_messages=deque(),
    )

    @s.ready_method
    def recv():
      return len(s.output_messages) != 0

    @s.model_method
    def recv():
      return s.output_messages.popleft()

    @s.ready_method
    def send():
      return 1

    @s.model_method
    def send(msg):
      s.received_messages.append(msg)
