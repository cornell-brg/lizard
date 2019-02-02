import abc
from inspect import getargspec, ismethod
from functools import wraps


class HardwareModel(object):

  __metaclass__ = abc.ABCMeta

  def __init__(s, interface, validate_args=True):
    s.interface = interface
    s.model_methods = {}
    s.validate_args = validate_args

  def reset(s):
    s._pre_cycle_wrapper()
    s._reset()
    s.cycle()

  @abc.abstractmethod
  def line_trace(s):
    pass

  @abc.abstractmethod
  def _pre_call(s, func, method, call_index):
    pass

  @abc.abstractmethod
  def _post_call(s, func, method, call_index):
    pass

  def _pre_cycle_wrapper(s):
    s.back_prop_tracking = []
    s._pre_cycle()

  def _post_cycle_wrapper(s):
    s._post_cycle()

  @abc.abstractmethod
  def _pre_cycle(s):
    pass

  @abc.abstractmethod
  def _post_cycle(s):
    pass

  @abc.abstractmethod
  def _reset(s):
    pass

  @staticmethod
  def validate(func):

    @wraps(func)
    def validate_init(s, *args, **kwargs):
      result = func(s, *args, **kwargs)
      if len(s.model_methods) != len(s.interface.methods):
        raise ValueError('Not all methods from interface implemented')
      return result

    return validate_init

  def model_method(s, func):
    if func.__name__ in s.model_methods:
      raise ValueError('Duplicate function: {}'.format(func.__name__))
    if func.__name__ not in s.interface.methods:
      raise ValueError('Method not in interface: {}'.format(func.__name__))
    if ismethod(func):
      raise ValueError('Expected function, got method: {}'.format(
          func.__name__))

    method = s.interface.methods[func.__name__]
    if s.validate_args:
      arg_spec = getargspec(func)
      for arg in arg_spec.args:
        if not isinstance(arg, str):
          raise ValueError('Illegal argument nest in function: {}'.format(
              func.__name__))
        if arg not in method.args:
          raise ValueError('Argument not found: {} in function: {}'.format(
              arg, func.__name__))
      if len(arg_spec.args) != len(method.args):
        raise ValueError('Incorrect number of arguments in function: {}'.format(
            func.__name__))
      if arg_spec.varargs is not None:
        raise ValueError('Function must have no *args: {}'.format(
            func.__name__))
      if arg_spec.keywords is not None:
        raise ValueError('Function must have no *kwargs: {}'.format(
            func.__name__))

    s.model_methods[func.__name__] = func

    @wraps(func)
    def wrapper(_call_index, *args, **kwargs):
      method = s.interface.methods[func.__name__]

      s._pre_call(func, method, _call_index)
      # call this method
      result = func(*args, **kwargs)
      s._post_call(func, method, _call_index)

      # interpret the result
      if isinstance(result, NotReady):
        # Make sure this method is permitted to be not ready
        if not method.rdy:
          raise ValueError(
              'Method returned NotReady but has no rdy signal: {}'.format(
                  func.__name__))
      else:
        # Normalize an empty to return to a length 0 result
        if result is None:
          result = Result()

        returned_size = 1
        if isinstance(result, Result):
          returned_size = result._size

        if len(method.rets) != returned_size:
          raise ValueError(
              'CL function {}: incorrect return size: expected: {} actual: {}'
              .format(func.__name__, len(method.rets), returned_size))

        # Normalize a singleton return into a result
        if not isinstance(result, Result):
          result = Result(**{method.rets.keys()[0]: result})

      # Log the result in the back_prop_tracking
      # This is used to ensure that when a future method is called
      # the result to a prior method doesn't mutate
      s._back_prop_track(method.name, _call_index, result)
      return result

    setattr(s, func.__name__, MethodDispatcher(wrapper))

  def cycle(s):
    s._post_cycle_wrapper()
    s._pre_cycle_wrapper()

  @staticmethod
  def _freeze_bits(data):
    if isinstance(data, list):
      return [HardwareModel._freeze_bits(x) for x in data]
    else:
      return int(data)

  @staticmethod
  def _freeze_result(result):
    frozen = {}
    for name, value in result._data.iteritems():
      frozen[name] = HardwareModel._freeze_bits(value)
    return frozen

  def _back_prop_track(s, method_name, call_index, result):
    s.back_prop_tracking.append((method_name, call_index, result,
                                 s._freeze_result(result)))

    for method_name, call_index, result, frozen in s.back_prop_tracking:
      if s._freeze_result(result) != frozen:
        raise ValueError(
            'Illegal backpropagation detected on method: {}[{}]'.format(
                method_name, call_index))


class NotReady(object):
  pass


class Result(object):

  def __init__(s, **kwargs):
    s._size = len(kwargs)
    s._data = {}
    for k, v in kwargs.items():
      s._data[k] = v
      setattr(s, k, v)


class MethodDispatcher(object):

  def __init__(s, wrapper_func):
    s.wrapper_func = wrapper_func

  def __getitem__(s, key):

    def index_dispatch(*args, **kwargs):
      return s.wrapper_func(key, *args, **kwargs)

    return index_dispatch

  def __call__(s, *args, **kwargs):
    return s[None](*args, **kwargs)
