from model.hardware_model import HardwareModel


class FLModel(HardwareModel):

  def __init__(s, interface):
    super(CLModel, s).__init__(interface)

  def _cycle(s):
    pass

  def _pre_call(s, func, method):
    pass

  def _post_call(s, func, method):
    pass

  def _pre_cycle(s):
    pass

  def _post_cycle(s):
    pass

  def line_trace(s):
    pass
