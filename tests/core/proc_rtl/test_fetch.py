from pymtl import *
from tests.context import lizard
from lizard.util.rtl.interface import Interface
from lizard.util.rtl.method import MethodSpec
from lizard.core.rtl.frontend.fetch import FetchInterface
from lizard.core.rtl.messages import FetchMsg
from lizard.model.hardware_model import HardwareModel, Result
from lizard.model.flmodel import FLModel
from collections import deque
from lizard.core.rtl.frontend.fetch import FetchInterface

TestFetchInterface = FetchInterface


class TestFetchFL(FLModel):

  @HardwareModel.validate
  def __init__(s, fetch_msgs):
    super(TestFetchFL, s).__init__(TestFetchInterface())

    s.state(fetch_msgs=deque(fetch_msgs))

    @s.ready_method
    def peek():
      return len(s.fetch_msgs) != 0

    @s.model_method
    def peek():
      return s.fetch_msgs[0]

    @s.model_method
    def take():
      s.fetch_msgs.popleft()
