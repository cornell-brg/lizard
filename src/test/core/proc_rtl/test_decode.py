from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from core.rtl.frontend.fetch import FetchInterface
from core.rtl.messages import DecodeMsg
from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from collections import deque


class TestDecodeInterface(Interface):

  def __init__(s):
    super(TestDecodeInterface, s).__init__([
        MethodSpec(
            'get',
            args={},
            rets={
                'msg': DecodeMsg(),
            },
            call=True,
            rdy=True,
        ),
    ])


class TestDecodeFL(FLModel):

  @HardwareModel.validate
  def __init__(s, decode_msgs):
    super(TestDecodeFL, s).__init__(TestDecodeInterface())

    s.state(decode_msgs=deque(decode_msgs))

    @s.ready_method
    def get():
      return len(s.decode_msgs) != 0

    @s.model_method
    def get():
      return s.decode_msgs.popleft()
