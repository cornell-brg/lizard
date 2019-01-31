import abc
from inspect import getargspec, ismethod
from functools import wraps


class HardwareModel(object):

  __metaclass__ = abc.ABCMeta

  def __init__(s, interface):
    s.interface = interface
    s.model_methods = {}

  @abc.abstractmethod
  def reset():
    pass

  @abc.abstractmethod
  def line_trace():
    pass

  @abc.abstractmethod
  def _cycle():
    pass

  @abc.abstractmethod
  def _pre_call(func, method):
    pass

  @abc.abstractmethod
  def _pre_cycle(s):
    pass

  @abc.abstractmethod
  def _post_cycle(s):
    pass

  def model_method(s, func):
    if func.__name__ in s.model_methods:
      raise ValueError('Duplicate function: {}'.format(func.__name__))
    if func.__name__ not in s.methods():
      raise ValueError('Method not in interface: {}'.format(func.__name__))
    if not ismethod(func):
      raise ValueError('Expected method, got function: {}'.format(
          func.__name__))

    arg_spec = getargspec(func)
    method = s.interface.methods[func.__name__]
    for arg in arg_spec.args:
      if not isinstance(arg, str):
        raise ValueError('Illegal argument nest in function: {}'.format(
            func.__name__))
      if arg not in method.args:
        raise ValueError('Argument not found: {} in functiOn: {}'.format(
            arg, func.__name__))
    if len(arg_spec.args) != len(method.args):
      raise ValueError('Extra arguments in function: {}'.format(func.__name__))

    s.model_methods[func.__name__] = func

    @wraps(func)
    def wrapper(*args, **kwargs):
      method = s.interface.methods[func.__name__]
      s._pre_call(func, method)

      # call this method
      result = func(s, *args, **kwargs)

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
          returned_size = result.size

        if len(method.rets) != returned_size:
          raise ValueError(
              'CL function: incorrect return size: expected: {} actual: {}'
              .format(func.__name__, len(method.rets), returned_size))

        # Normalize a singleton return into a result
        if not isinstance(result, Result):
          result = Result(**{method.rets.keys()[0]: result})

      return result

    setattr(s, func.__name__, wrapper)

  def cycle(s):
    s._pre_cycle()
    s._cycle()
    s._post_cycle()

  def validate(s):
    if len(s.model_methods) != len(s.interface.methods):
      raise ValueError('Not all methods from interface implemented')


class NotReady:
  pass


class Result:

  def __init__(s, **kwargs):
    size = len(kwargs)
    for k, v in kwargs.items():
      setattr(s, k, v)
