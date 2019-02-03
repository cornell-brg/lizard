from pymtl import *
from util.rtl.interface import Interface
from model.hardware_model import NotReady, Result
from model.clmodel import CLModel
from model.rtlwrapper import RTLWrapper


class CLAdapter(Model):

  def __init__(s, clmodel):
    s.cl = clmodel
    s.interface = s.cl.interface
    s.interface.apply(s)
    s.cl.reset()
    # start with one snapshot in case compute is called before cycle
    s.cl.snapshot()

    # Uses to force the compute block to run at least once per cycle
    # The tick_rtl block toggles this every cycle, and we put it in the
    # sensitivity list of the compute block
    # Without this, if you have the same inputs to the module for 2 cycles
    # in a row, the compute block will not run.
    # It should though, because it depends on internal state which
    # updates on a cycle edge.
    s.whatever_you_do_make_sure_no_method_has_this_name = Wire(1)

    def compute():
      # before we recomupte everything, must restore to the start of the cycle
      s.cl.restore()

      for method_name, method in s.interface.methods.iteritems():
        cl_method_dispatcher = getattr(s.cl, method_name)
        for instance in range(method.num_permitted_calls()):
          # since we set everything in a giant block, it could be that ready is
          # true from the last cycle, and some other block in the design sees that,
          # and sets call this cycle. But, then this block sets ready to false,
          # but sees that call is true, so invokes anyway. That can't happen,
          # so we check ready before invoking. If we set ready to false,
          # and call is true, whatever set call will see that and must lower call
          # (or else be in violation of the spec)
          safe_to_call = True
          if method.rdy:
            # This will read the ready of the current port in CL
            safe_to_call = cl_method_dispatcher.rdy(instance)
            s.resolve_port(method, 'rdy', instance).v = safe_to_call

          if safe_to_call and (not method.call or
                               s.resolve_port(method, 'call', instance)):
            kwargs = {
                arg_name: s.resolve_port(method, arg_name, instance)
                for arg_name in method.args.keys()
            }
            # Auto-dispatch, advancing to the next port in CL
            result = cl_method_dispatcher(**kwargs)

            if isinstance(result, NotReady):
              raise ValueError('Method called when not ready')
          else:
            # generate a zero result
            ret_dict = {}
            for ret_name, ret_type in method.rets.iteritems():
              ret_dict[ret_name] = CLModel._gen_zero(ret_type)
            result = Result(**ret_dict)

            # Advance to the next CL port
            s.cl._advance()

          # at this point we have a result no matter what, write it out
          for ret_name, ret_value in result._data.iteritems():
            RTLWrapper._set_inputs(
                s.resolve_port(method, ret_name, instance), ret_value)

    def generate_senses():
      senses = [s.whatever_you_do_make_sure_no_method_has_this_name]
      for method_name, method in s.interface.methods.iteritems():
        for instance in range(method.num_permitted_calls()):
          if method.call:
            senses.append(s.resolve_port(method, 'call', instance))
          for arg_name in method.args.keys():
            s.rec_add(s.resolve_port(method, arg_name, instance), senses)
      return [sense._target_bits for sense in senses]

    compute.generate_senses = generate_senses
    s.combinational(compute)

    @s.tick_rtl
    def cycle():
      if s.reset():
        s.whatever_you_do_make_sure_no_method_has_this_name.n = 0
        s.cl.reset()
      else:
        s.whatever_you_do_make_sure_no_method_has_this_name.n = ~s.whatever_you_do_make_sure_no_method_has_this_name
        s.cl.cycle()
      # snapshot at the start of each cycle
      s.cl.snapshot()

  def resolve_port(s, method, name, instance):
    # model.<method_name>_<port_name>
    base_port = getattr(s, Interface.mangled_name('', method.name, name))
    # if there are multiple instances of this method, get the current one
    if method.count is not None:
      base_port = base_port[instance]

    return base_port

  @staticmethod
  def rec_add(source, target):
    if isinstance(source, list):
      for x in source:
        CLAdapter.rec_add(x, target)
    else:
      target.append(source)
