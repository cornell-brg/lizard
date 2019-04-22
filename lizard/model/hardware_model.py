import abc
from inspect import getargspec
from functools import wraps
from lizard.util.pretty_print import list_string_value
from lizard.bitutil import copy_bits
from copy import deepcopy


class HardwareModel(object):

  __metaclass__ = abc.ABCMeta

  def __init__(s, interface):
    s.interface = interface
    s.model_methods = {}
    s.ready_methods = {}
    s.state_element_names = []
    s.saved_state = {}
    s.state_reset_values = {}
    s.anonymous_state_counter = 0

  def reset(s):
    s._pre_cycle_wrapper()
    s._reset()
    for name, state_element in s._state_elements():
      if isinstance(state_element, HardwareModel):
        state_element.reset()
      else:
        setattr(s, name, deepcopy(s.state_reset_values[name]))
    s.cycle()

  @abc.abstractmethod
  def line_trace(s):
    pass

  @abc.abstractmethod
  def _pre_call(s, method, call_index):
    pass

  @abc.abstractmethod
  def _post_call(s, method, call_index):
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

  def _reset(s):
    pass

  def state(s, **kwargs):
    for k, v in kwargs.iteritems():
      if hasattr(s, k):
        raise ValueError('Member already present: {}'.foramt(k))
      else:
        setattr(s, k, v)
        s.state_element_names.append(k)
        # save the initial value if not a hardware model
        if not isinstance(v, HardwareModel):
          s.state_reset_values[k] = deepcopy(v)

  def register_state(s, hardware_model):
    if not isinstance(hardware_model, HardwareModel):
      raise ValueError('Must be HardwareModel')
    name = '_anonymous_state_member_{}'.format(s.anonymous_state_counter)
    s.anonymous_state_counter += 1
    s.state(**{name: hardware_model})

  def _state_elements(s):
    return [(name, getattr(s, name)) for name in s.state_element_names]

  def snapshot_model_state(s):
    s.extra_model_state = s._snapshot_model_state()
    for name, state_element in s._state_elements():
      if isinstance(state_element, HardwareModel):
        state_element.snapshot_model_state()
      else:
        s.saved_state[name] = deepcopy(state_element)

  def restore_model_state(s):
    s._pre_cycle_wrapper()
    s._restore_model_state(s.extra_model_state)
    for name, state_element in s._state_elements():
      if isinstance(state_element, HardwareModel):
        state_element.restore_model_state()
      else:
        setattr(s, name, deepcopy(s.saved_state[name]))

  def _snapshot_model_state(s):
    pass

  def _restore_model_state(s, state):
    pass

  @staticmethod
  def validate(func):

    @wraps(func)
    def validate_init(s, *args, **kwargs):
      result = func(s, *args, **kwargs)
      if len(s.model_methods) != len(s.interface.methods):
        raise ValueError('Not all methods from interface implemented')

      # Ensure every method that is supposed to have a ready signal has one
      for name, method in s.interface.methods.iteritems():
        if method.rdy and name not in s.ready_methods:
          raise ValueError(
              'Method has rdy signal but no ready method: {}'.format(name))

      return result

    return validate_init

  def _check_method(s, name, method_dict):
    if name in method_dict:
      raise ValueError('Duplicate function: {}'.format(name))
    if name not in s.interface.methods:
      raise ValueError('Method not in interface: {}'.format(name))

  def ready_method(s, func):
    s.ready_method_explicit(func.__name__, func, True)

  def ready_method_explicit(s, name, func_like, validate_args):
    s._check_method(name, s.ready_methods)
    if validate_args:
      arg_spec = getargspec(func_like)
      if len(
          arg_spec.args
      ) != 1 or arg_spec.varargs is not None or arg_spec.keywords is not None:
        raise ValueError(
            'Ready function must take exactly 1 argument (call_index)')
    s.ready_methods[name] = func_like

  def model_method(s, func):
    s.model_method_explicit(func.__name__, func, True)

  def model_method_explicit(s, name, func_like, validate_args):
    s._check_method(name, s.model_methods)

    method = s.interface.methods[name]
    if validate_args:
      arg_spec = getargspec(func_like)
      for arg in arg_spec.args:
        if not isinstance(arg, str):
          raise ValueError('Illegal argument nest in function: {}'.format(name))
        if arg not in method.args:
          raise ValueError('Argument not found: {} in function: {}'.format(
              arg, name))
      if len(arg_spec.args) != len(method.args):
        raise ValueError(
            'Incorrect number of arguments in function: {}'.format(name))
      if arg_spec.varargs is not None:
        raise ValueError('Function must have no *args: {}'.format(name))
      if arg_spec.keywords is not None:
        raise ValueError('Function must have no *kwargs: {}'.format(name))

    s.model_methods[name] = func_like

    def wrapper(_call_index, *args, **kwargs):
      method = s.interface.methods[name]

      s._pre_call(method, _call_index)
      # check to see if the method is ready
      if name in s.ready_methods and not s.ready_methods[name](_call_index):
        result = not_ready_instance
      else:
        # call this method
        result = func_like(*args, **kwargs)
        if isinstance(result, NotReady):
          raise ValueError(
              'Method may not return not ready -- use ready_method decorator')
      s._post_call(method, _call_index)

      # interpret the result
      if not isinstance(result, NotReady):
        # Normalize an empty to return to a length 0 result
        if result is None:
          result = Result()

        returned_size = 1
        if isinstance(result, Result):
          returned_size = result._size

        if len(method.rets) != returned_size:
          raise ValueError(
              'CL function {}: incorrect return size: expected: {} actual: {}'
              .format(name, len(method.rets), returned_size))

        if isinstance(
            result,
            Result) and set(method.rets.keys()) != set(result._data.keys()):
          raise ValueError(
              'CL function {}: incorrect return names: expected: {} actual: {}'
              .format(name, list_string_value(method.rets.keys()),
                      list_string_value(result._data.keys())))

        # Normalize a singleton return into a result
        if not isinstance(result, Result):
          result = Result(**{method.rets.keys()[0]: result})

      # Log the result in the back_prop_tracking
      # This is used to ensure that when a future method is called
      # the result to a prior method doesn't mutate
      s._back_prop_track(method.name, _call_index, result)

      # Freeze the result so if the caller preserves it across multiple cycles it doesn't change
      return s._freeze_result(result)

    if hasattr(s, name):
      raise ValueError('Internal wrapper error')

    setattr(s, name, MethodDispatcher(name, wrapper, s.ready_methods))

  def cycle(s):
    s._post_cycle_wrapper()
    s._pre_cycle_wrapper()

  @staticmethod
  def _freeze_result(result):
    result = HardwareModel._freeze_result_to_dict(result)
    if isinstance(result, NotReady):
      return result
    else:
      return Result(**result)

  @staticmethod
  def _freeze_result_to_dict(result):
    if isinstance(result, NotReady):
      return result
    frozen = {}
    for name, value in result._data.iteritems():
      frozen[name] = copy_bits(value)
    return frozen

  def _back_prop_track(s, method_name, call_index, result):
    s.back_prop_tracking.append((method_name, call_index, result,
                                 s._freeze_result_to_dict(result)))

    for method_name, call_index, result, frozen in s.back_prop_tracking:
      if s._freeze_result_to_dict(result) != frozen:
        raise ValueError(
            'Illegal backpropagation detected on method: {}[{}]'.format(
                method_name, call_index))


class NotReady(object):
  _created = False

  def __init__(s):
    if NotReady._created:
      raise ValueError('singleton')
    else:
      NotReady._created = True


not_ready_instance = NotReady()


class Result(object):

  def __init__(s, **kwargs):
    s._size = len(kwargs)
    s._data = {}
    for k, v in kwargs.items():
      s._data[k] = v
      setattr(s, k, v)

  def copy(s):
    temp = {}
    for k, v in s._data.iteritems():
      temp[k] = copy_bits(v)
    return Result(**temp)

  def __str__(s):
    return '[{}]'.format(', '.join(
        '{}={}'.format(k, v) for k, v in s._data.iteritems()))


class MethodDispatcher(object):

  def __init__(s, name, wrapper_func, ready_dict):
    s.name = name
    s.wrapper_func = wrapper_func
    s.ready_dict = ready_dict

  def rdy(s, call_index=None):
    return s.ready_dict[s.name](call_index)

  def __getitem__(s, key):

    def index_dispatch(*args, **kwargs):
      return s.wrapper_func(key, *args, **kwargs)

    return index_dispatch

  def __call__(s, *args, **kwargs):
    return s[None](*args, **kwargs)
