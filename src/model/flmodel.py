from model.hardware_model import HardwareModel


class FLModel(HardwareModel):

  def __init__(s, interface):
    super(FLModel, s).__init__(interface)

  def ready_method_explicit(s, name, func_like, validate_args):
    # We can't really validate the args of func, which is what validate_args means

    def ignore_call_index_wrapper(call_index):
      return func_like()

    super(FLModel, s).ready_method_explicit(name, ignore_call_index_wrapper,
                                            True)

  def _cycle(s):
    pass

  def _pre_call(s, method, call_index):
    pass

  def _post_call(s, method, call_index):
    pass

  def _pre_cycle(s):
    pass

  def _post_cycle(s):
    pass

  def line_trace(s):
    pass
