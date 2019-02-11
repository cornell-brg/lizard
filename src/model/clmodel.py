from pymtl import *
from model.hardware_model import HardwareModel
from util.rtl.types import Array


class CLModel(HardwareModel):

  def __init__(s, interface, validate_args=True):
    super(CLModel, s).__init__(interface, validate_args=validate_args)

    s.methods = s.interface.methods.values()
    s.index_map = {s.methods[i].name: i for i in range(len(s.methods))}

  def _pre_call(s, func, method, call_index):
    method_index = s.index_map[func.__name__]

    # if all done
    if s.sequence_method == len(s.methods):
      raise ValueError('All methods invoked already; call cycle()')
    # if the method was a prior method
    elif method_index < s.sequence_method:
      raise ValueError('Illegal method order')
    # if same method ensure it has calls left
    elif method_index == s.sequence_method:
      # If no index specified pick the latest one
      call_index = call_index or s.sequence_call
    else:
      # For a future method with no index pick the first one
      call_index = call_index or 0

    # advance to it, calling any methods without a call
    # signal in between
    s._drain_to(method_index, call_index)

  def _advance(s):
    s.sequence_call += 1
    if s.sequence_call == s.methods[s.sequence_method].num_permitted_calls():
      s.sequence_call = 0
      s.sequence_method += 1

  def _post_call(s, func, method, call_index):
    s._advance()

  def _pre_cycle(s):
    # initialize to the first method in the interface
    s.sequence_method = 0
    # initialize to 0 calls of that method
    s.sequence_call = 0

  def _post_cycle(s):
    # drain all remaining methods
    s._drain_to(len(s.methods), -1)

  def _reset(s):
    # prevent any methods from running after the reset
    s.sequence_method = len(s.methods)
    s.sequence_call = -1

  def _skip(s):
    result = None
    current_method = s.methods[s.sequence_method]
    if not current_method.call:
      # Default all the arguments to 0
      arg_dict = {}
      for name, pymtl_type in current_method.args.iteritems():
        arg_dict[name] = s._gen_zero(pymtl_type)
      # invoke the method
      result = getattr(s, current_method.name)(**arg_dict)
    else:
      s._advance()
    return result

  def _drain_to(s, method_index, call_index):

    if method_index < len(s.methods):
      limit = s.methods[method_index].num_permitted_calls()
      if call_index == -1:
        call_index = limit - 1
      elif call_index >= limit:
        raise ValueError(
            'call_index too high for method: got: {} limit: {}'.format(
                call_index, limit))

    while (s.sequence_method, s.sequence_call) < (method_index, call_index):
      s._skip()

  @staticmethod
  def _gen_zero(pymtl_type):
    if isinstance(pymtl_type, Bits):
      result = pymtl_type()
      result._uint = 0
      return result
    elif isinstance(pymtl_type, Array):
      return [
          CLModel._gen_zero(pymtl_type.Data) for _ in range(pymtl_type.length)
      ]
    else:
      raise ValueError('Unknown type: {}'.format(type(pymtl_type)))
