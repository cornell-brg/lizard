from pymtl import *
from util.rtl.interface import Interface
from model.hardware_model import NotReady, Result
from model.clmodel import CLModel
from model.rtlwrapper import RTLWrapper

class CLAdapter(Model):
  def __init__(s, clmodel):
    s.cl = clmodel
    s.cl.interface.apply(s)

    @s.combinational
    def compute():
      # before we recomupte everything, must restore to the start of the cycle
      s.cl._restore()

      for method_name, method in s.cl.interface.methods.iteritems():
        cl_method_dispatcher = getattr(s.cl, method_name)
        for instance in range(method.num_permitted_calls()):
          if method.rdy:
            s.resolve_port(method, 'rdy', instance).v = cl_method_dispatcher.rdy()
          
          if method.call:
            if s.resolve_port(method, 'call', instance):
              kwargs = {arg_name: s.resolve_port(method, arg_name, instance) for arg_name in method.args.keys()}
              result = cl_method_dispatcher(**kwargs)

              if isinstance(result, NotReady):
                raise ValueError('Method called when not ready')
            else:
              # generate a zero result
              ret_dict = {}
              for ret_name, ret_type in method.rets.iteritems():
                ret_dict[ret_name] = CLModel._get_zero(ret_type)
              result = Result(**ret_dict)
          else:
            # skip the method, which will call it if has no call
            result = s.cl._skip()

          # at this point we have a result no matter what, write it out
          for ret_name, ret_value in result._data.iteritems():
            RTLWrapper._set_inputs(s.resolve_port(method, ret_name, instance), ret_value)

    @s.tick_rtl
    def cycle():
      if s.reset():
        s.cl.reset()
      else:
        s.cl.cycle()

      # snapshot at the start of each cycle
      s.cl.snapshot()

  def resolve_port(s, method, name, instance):
    # model.<method_name>_<port_name>
    base_port = getattr(s, Interface.mangled_name('', method.name, name))
    # if there are multiple instances of this method, get the current one
    if method.count is not None:
      base_port = base_port[instance]

