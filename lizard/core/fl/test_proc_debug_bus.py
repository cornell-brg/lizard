from collections import deque
from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel


class TestProcDebugBusFL(FLModel):

  @HardwareModel.validate
  def __init__(s, interface, output_messages=None):
    super(TestProcDebugBusFL, s).__init__(interface)

    if output_messages is None:
      output_messages = []
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
