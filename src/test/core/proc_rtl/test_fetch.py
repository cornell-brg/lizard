from pymtl import *
from util.rtl.interface import Interface
from util.rtl.method import MethodSpec
from core.rtl.frontend.fetch import FetchInterface
from core.rtl.messages import FetchMsg
from model.hardware_model import HardwareModel, Result
from model.flmodel import FLModel
from collections import deque
from core.rtl.frontend.fetch import FetchInterface

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
