from pymtl import *

from model.hardware_model import HardwareModel
from model.clmodel import CLModel
from model.hardware_model import NotReady, Result

from util.rtl.interface import Interface


class RTLWrapper(CLModel):

  @HardwareModel.validate
  def __init__(s, rtl_model):
    super(RTLWrapper, s).__init__(rtl_model.interface, False)
    s.model = rtl_model
    s.model.elaborate()
    s.sim = SimulationTool(s.model)

    for method_name in s.interface.methods.keys():
      s.model_method(s._gen_wrapper_function(method_name))

  def _gen_wrapper_function(s, method_name):

    def wrapper(*args, **kwargs):
      method = s.interface[method_name]

      # validate all the arguments
      if len(args) != 0:
        # can only accept non-keyword arguments if the method takes 1 parameter
        if len(method.args) != 1:
          raise ValueError(
              'Method takes more than one argument; all arguments must be keyword arguments'
          )
        # kwargs better also be empty
        if len(kwargs) != 0:
          raise ValueError('Too many arguments')
        # move it to kwargs
        kwargs[method.args.keys()[0]] = args[0]

      for name, _ in kwargs.iteritems():
        if name not in method.args:
          raise ValueError('Unknown method argument: {}'.format(name))
      if len(method.args) != len(kwargs):
        raise ValueError('Not all arguments provided')

      # check the rdy signal, if present
      if method.rdy:
        s.sim.eval_combinational()
        # model.<method_name>_rdy
        rdy_port = getattr(s.model,
                           Interface.mangled_name('', method_name, 'rdy'))
        if rdy_port == 0:
          return NotReady()

      # set all the input ports
      for name, value in kwargs.iteritems():
        # model.<method_name>_<port_name>
        base_port = getattr(s.model,
                            Interface.mangled_name('', method_name, name))
        # if there are multiple instances of this method, get the current one
        if method.count is not None:
          base_port = base_port[s.sequence_call]

        # base_port is potentially now still list of of ports if the method
        # type is array
        s._set_inputs(base_port, value)

      # set the call signal, if present
      if method.call:
        # model.<method_name>_call
        call_port = getattr(s.model,
                            Interface.mangled_name('', method_name, 'call'))
        call_port.v = 1

      # extract the result
      s.sim.eval_combinational()
      result_dict = {}
      for name, _ in method.rets.iteritems():
        base_port = getattr(s.model,
                            Interface.mangled_name('', method_name, name))
        # if there are multiple instances of this method, get the current one
        if method.count is not None:
          base_port = base_port[s.sequence_call]
        result_dict[name] = base_port

      return Result(**result_dict)

    wrapper.__name__ = method_name
    return wrapper

  @staticmethod
  def _list_apply(left, right, func):
    if isinstance(left, list) != isinstance(right, list):
      raise ValueError(
          'Array mismatch: type(left) = {}, type(right) = {}'.format(
              type(left), type(right)))

    if isinstance(left, list):
      if len(left) != len(right):
        raise ValueError(
            'Array mismatch: len(left) = {}, len(right) = {}'.format(
                len(left), len(right)))
      for l, r in zip(left, right):
        RTLWrapper._list_apply(l, r, func)
    else:
      func(left, right)

  @staticmethod
  def _set_inputs(in_ports, values):

    def set(left, right):
      left.v = right

    RTLWrapper._list_apply(in_ports, values, set)

  def _reset(s):
    s.sim.reset()

  def line_trace(s):
    s.sim.eval_combinational()
    return "{:>3}: {}".format(s.sim.ncycles, s.model.line_trace())

  def _pre_cycle(s):
    super(RTLWrapper, s)._pre_cycle()
    # Initially, set the call signals set the call signal, if present
    for method_name, method in s.interface.methods.iteritems():
      if method.call:
        # model.<method_name>_call
        call_port = getattr(s.model,
                            Interface.mangled_name('', method_name, 'call'))
        call_port.v = 0

  def _post_cycle(s):
    super(RTLWrapper, s)._post_cycle()
    s.sim.cycle()
