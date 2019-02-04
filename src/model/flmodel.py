from model.hardware_model import HardwareModel


class FLModel(HardwareModel):

  def __init__(s, interface, validate_args=True):
    super(FLModel, s).__init__(interface, validate_args=validate_args)

  def ready_method(s, func):

    def ignore_call_index_wrapper(call_index):
      return func()

    ignore_call_index_wrapper.__name__ = func.__name__
    super(FLModel, s).ready_method(ignore_call_index_wrapper)

  def _cycle(s):
    pass

  def _pre_call(s, func, method, call_index):
    pass

  def _post_call(s, func, method, call_index):
    pass

  def _pre_cycle(s):
    pass

  def _post_cycle(s):
    pass

  def line_trace(s):
    pass
