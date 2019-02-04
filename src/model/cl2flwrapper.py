from model.flmodel import FLModel


class CL2FLWrapper(FLModel):

  def __init__(s, clmodel):
    super(FLModel, s).__init__(clmodel.interface, validate_args=False)
    s.cl = clmodel

    for method_name in s.interface.methods.keys():
      wrapper, ready = s._gen_wrapper_function(method_name)
      s.model_method(wrapper)
      if ready is not None:
        s.ready_method(ready)

  def _reset(s):
    s.cl.reset()

  def _snapshot_model_state(s):
    s.cl.snapshot_model_state()

  def _restore_model_state(s, state):
    s.cl.restore_model_state()

  def _gen_wrapper_function(s, method_name):
    method = s.interface.methods[method_name]

    def wrapper(*args, **kwargs):
      result = getattr(s.cl, method_name)(*args, **kwargs)
      # Cycling might change the result, so copy it
      result = result.copy()
      s.cl.cycle()
      return result

    wrapper.__name__ = method_name

    if method.rdy:

      def ready():
        # always use the 0th call index, since we cycle after every call,
        # no later method will ever get called
        return getattr(s.cl, method_name).rdy(0)

      ready.__name__ = method_name
    else:
      ready = None

    return wrapper, ready
