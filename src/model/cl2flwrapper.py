from model.flmodel import FLModel


class CL2FLWrapper(FLModel):

  def __init__(s, clmodel):
    super(FLModel, s).__init__(clmodel.interface)
    s.state(cl=clmodel)

    for method_name in s.interface.methods.keys():
      wrapper, ready = s._gen_wrapper_function(method_name)
      s.model_method_explicit(method_name, wrapper, False)
      if ready is not None:
        s.ready_method_explicit(method_name, ready, False)

  def _gen_wrapper_function(s, method_name):
    method = s.interface.methods[method_name]

    def wrapper(*args, **kwargs):
      result = getattr(s.cl, method_name)(*args, **kwargs)
      # Cycling might change the result, so copy it
      result = result.copy()
      s.cl.cycle()
      return result

    if method.rdy:

      def ready():
        # always use the 0th call index, since we cycle after every call,
        # no later method will ever get called
        return getattr(s.cl, method_name).rdy(0)
    else:
      ready = None

    return wrapper, ready
