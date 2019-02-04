from model.clmodel import CLModel


class FL2CLWrapper(CLModel):

  def __init__(s, flmodel):
    super(FL2CLWrapper, s).__init__(flmodel.interface, validate_args=False)
    s.fl = flmodel

    s.ready_states = {}
    for method_name, method in s.interface.methods.iteritems():
      if method.rdy:
        s.ready_states[method_name] = 0

      wrapper, ready = s._gen_wrapper_function(method_name)
      s.model_method(wrapper)
      if ready is not None:
        s.ready_method(ready)

  def _gen_wrapper_function(s, method_name):
    method = s.interface.methods[method_name]

    def wrapper(*args, **kwargs):
      return getattr(s.fl, method_name)(*args, **kwargs)

    wrapper.__name__ = method_name

    if method.rdy:

      def ready(call_index):
        next_call_index = s.ready_states[method_name]
        # if asking about index before the next call,
        # it must have been ready (since it was called)
        if call_index < next_call_index:
          return True
        else:
          return s.fl.ready_methods[method.name](call_index)

      ready.__name__ = method_name
    else:
      ready = None

    return wrapper, ready

  def _pre_cycle(s):
    super(FL2CLWrapper, s)._pre_cycle()

    for method_name in s.ready_states.keys():
      s.ready_states[method_name] = 0

  def _pre_call(s, func, method, call_index):
    super(FL2CLWrapper, s)._pre_call(func, method, call_index)

    if method.rdy:
      # advance the ready boundary to the next method if the method is ready
      call_index = call_index or 0
      if s.fl.ready_methods[method.name](call_index):
        s.ready_states[method.name] = call_index + 1

  def _reset(s):
    s.fl.reset()

  def _snapshot(s):
    s.fl.snapshot()

  def _restore(s):
    s.fl.restore()

  def line_trace(s):
    return ''
