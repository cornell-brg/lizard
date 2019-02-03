import copy
import inspect
import hypothesis.strategies as st
from pymtl import *
from hypothesis.stateful import *
from hypothesis import settings
from hypothesis.vendor.pretty import CUnicodeIO, RepresentationPrinter
from sets import Set
from util.rtl.interface import Interface
from util.rtl.types import Array
from util.test_utils import create_test_bitstruct
import copy

debug = True


def _list_string(lst):
  return ", ".join([str(x) for x in lst])


def _list_string_value(lst):
  str_list = []
  for x in lst:
    if isinstance(x, BitStruct):
      str_list += [bitstruct_detail(x)]
    else:
      str_list += [str(x)]
  return ", ".join(str_list)


#-------------------------------------------------------------------------
# MethodBasedRuleStrategy
#-------------------------------------------------------------------------
class MethodBasedRuleStrategy(SearchStrategy):

  def __init__(self, machine):
    SearchStrategy.__init__(self)
    self.machine = machine
    self.rules = machine.method_rules()
    self.condition_rules = machine.condition_rules()
    self.always_rules = machine.always_rules()

  def do_draw(self, data):
    # This strategy draw a randomly selected number of rules and do not care about
    # validity. In execute_step(step), only valid rules will be fired. We do this to
    # test possible dependencies - some rules are not valid in the first place become
    # valid if some other rules fire in the same cycle
    n = len(self.condition_rules)
    rule_to_fire = self.always_rules[:]
    remaining_rules = [i for i in range(0, n)]
    num_rules = cu.integer_range(data, 1, n - 1)
    for _ in range(num_rules):
      i = cu.integer_range(data, 0, len(remaining_rules) - 1)
      rule_to_fire += [self.condition_rules[remaining_rules[i]]]
      del remaining_rules[i]

    rule_to_fire.sort(
      key=lambda rule: (
        self.machine.interface.methods.keys().index( rule.fl_method_name ),
        rule.rtl_method_name,
      )
    )
    if rule_to_fire:
      return [
          (rule, data.draw(rule.arguments_strategy)) for rule in rule_to_fire
      ]


#-------------------------------------------------------------------------
# TestStateMachine
#-------------------------------------------------------------------------
class RunMethodTestError(Exception):
  pass


class TestStateMachine(GenericStateMachine):
  __argument_strategies = {}
  __preconditions = {}
  __method_rules = {}
  __always_rules = {}
  __condition_rules = {}

  def __init__(self):
    super(TestStateMachine, self).__init__()
    self.__rules_strategy = MethodBasedRuleStrategy(self)
    self.__stream = CUnicodeIO()
    self.__printer = RepresentationPrinter(self.__stream)

  def _error_line_trace(self, method_line_trace, error_msg):
    self.sim.cycle(method_line_trace)
    if hasattr(self.reference, 'cycle'):
      self.reference.cycle()
    print "========================== error =========================="
    raise RunMethodTestError(error_msg)

  def _validate_result(self, m_ret_names, r_ret, method_name, arg,
                       method_line_trace):
    type_error_msg = """
   Reference and model have mismatched returns!
    - method name    : {method_name}
    - model ret      : {model_ret}
    - reference ret  : {reference_ret}
  """
    if not r_ret:
      if m_ret_names:
        error_msg = type_error_msg.format(
            method_name=method_name,
            model_ret=_list_string(m_ret_names),
            reference_ret="")
        self._error_line_trace(method_line_trace, error_msg)
      else:
        return

    if isinstance(r_ret, dict):
      r_ret_names = set(sorted(r_ret.keys()))
      if r_ret_names != m_ret_names:
        error_msg = type_error_msg.format(
            method_name=method_name,
            model_ret=_list_string(m_ret_names),
            reference_ret=_list_string(r_ret_names))
        self._error_line_trace(method_line_trace, error_msg)
    else:
      if not len(r_ret) == len(m_ret_names):
        error_msg = type_error_msg.format(
            method_name=method_name,
            model_ret=_list_string(m_ret_names),
            reference_ret=_list_string(r_ret))
        self._error_line_trace(method_line_trace, error_msg)

  def compare_result(self, m_result, r_result, method_name, arg,
                     method_line_trace):
    if isinstance(r_result, ReturnValues):
      r_result = r_result.__dict__

    if isinstance(m_result, ReturnValues):
      m_result = m_result.__dict__

    if r_result != None:
      if not isinstance(r_result, dict):
        r_result = [r_result] if isinstance(r_result, int) or isinstance(
            r_result, Bits) else list(r_result)
        r_result_list = r_result
      else:
        r_result_list = [value for (key, value) in sorted(r_result.items())]

    m_ret_names = set(sorted(m_result.keys()))
    self._validate_result(m_ret_names, r_result, method_name, arg,
                          method_line_trace)

    value_error_msg = """
   test state machine received an incorrect value!
    - method name    : {method_name}
    - arguments      : {arg}
    - ret name       : {ret_name}
    - expected value : {expected_msg}
    - actual value   : {actual_msg}
  """

    if r_result:
      # assume that results are in alphabetical order
      m_result_list = [value for (key, value) in sorted(m_result.items())]
      for m_result_value, r_result_value in zip(m_result_list, r_result_list):
        if r_result_value != '?' and not r_result_value == m_result_value:
          error_msg = value_error_msg.format(
              method_name=method_name,
              arg=arg,
              ret_name=_list_string(sorted(m_result.keys())),
              expected_msg=_list_string_value(r_result_list),
              actual_msg=_list_string_value(m_result_list))
          self._error_line_trace(method_line_trace, error_msg)

  def steps(self):
    return self.__rules_strategy

  def execute_step(self, step):
    # store result of sim and reference
    s_results = []
    r_results = []
    method_names = []
    data_list = []

    method_line_trace = []
    # go though all rules for this step
    for ruledata in step:
      rule, data = ruledata
      data = dict(data)

      # For dependency reason we do allow rules invalid in the first place
      # to be added to step.
      # See MethodBasedRuleStrategy for more
      if not self.is_valid(rule, data):
        continue

      data_list += [data]
      for k, v in list(data.items()):
        if isinstance(v, VarReference):
          data[k] = self.names_to_values[v.name]

      # For method based interface rules, call rdy ones only
      methods = self.interface.methods
      fl_name = rule.fl_method_name
      rtl_name = rule.rtl_method_name
      method_names += [rtl_name]
      sim_class_members = self.sim.__class__.__dict__
      reference_class_members = self.reference.__class__.__dict__

      hasrdy = methods[fl_name].rdy
      rdy = False
      if hasrdy:
        if sim_class_members[rtl_name + "_rdy"](self.sim):
          assert reference_class_members[fl_name + "_rdy"](self.reference)
          rdy = True
      if not hasrdy or rdy:
        if debug:
          argument_string = []
          for k, v in data.items():
            if isinstance(v, BitStruct):
              v = bitstruct_detail(v)
            argument_string += ["{}={}".format(k, v)]
          method_line_trace += [
              "{}( {} )".format(rtl_name, _list_string(argument_string))
              if argument_string else "{}()".format(rtl_name)
          ]
        s_results += [sim_class_members[rtl_name + "_call"](self.sim, **data)]
        r_results += [
            reference_class_members[fl_name + "_call"](self.reference, **data)
        ]

    method_line_trace = ",  ".join(method_line_trace)
    for s_result, r_result, method, data in zip(s_results, r_results,
                                                method_names, data_list):
      self.compare_result(s_result, r_result, method, data, method_line_trace)

    self.sim.cycle(method_line_trace)
    if hasattr(self.reference, 'cycle'):
      self.reference.cycle()

  def print_step(self, step):
    pass

  def is_valid(self, rule, data):
    if rule.precondition and not rule.precondition(self, data):
      return False
    return True

  @classmethod
  def add_argument_strategy(cls, method, arguments):
    target = cls.__argument_strategies.setdefault(cls, {})
    if target.has_key(method):
      error_msg = """
      A method cannot have two distince strategies. 
        method_name : {method_name}
      """.format(method_name=method)
      raise InvalidDefinition(error_msg)
    target[method] = arguments

  @classmethod
  def argument_strategy(cls, method):
    target = cls.__argument_strategies.setdefault(cls, {})
    return target.setdefault(method, {})

  @classmethod
  def _add_rule(cls, rules):
    target = cls.__method_rules.setdefault(cls, [])
    target += [rules]

  @classmethod
  def add_always_rule(cls, rules):
    target = cls.__always_rules.setdefault(cls, [])
    target += [rules]
    cls._add_rule(rules)

  @classmethod
  def add_condition_rule(cls, rules):
    target = cls.__condition_rules.setdefault(cls, [])
    target += [rules]
    cls._add_rule(rules)

  @classmethod
  def add_rule(cls, rules, hascall):
    if hascall:
      cls.add_condition_rule(rules)
    else:
      cls.add_always_rule(rules)

  @classmethod
  def method_rules(cls):
    target = cls.__method_rules.setdefault(cls, [])
    return target

  @classmethod
  def condition_rules(cls):
    target = cls.__condition_rules.setdefault(cls, [])
    return target

  @classmethod
  def always_rules(cls):
    target = cls.__always_rules.setdefault(cls, [])
    return target

  @classmethod
  def add_precondition(cls, method, precondition):
    target = cls.__preconditions.setdefault(cls, {})
    target[method] = precondition

  @classmethod
  def precondition(cls, method):
    target = cls.__preconditions.setdefault(cls, {})
    return target.setdefault(method, None)


#-------------------------------------------------------------------------
# WrapperClass
#-------------------------------------------------------------------------
class WrapperClass:
  methods = {}
  methods_fl = {}
  methods_clear = []

  def __init__(s, model):
    s.model = model
    s.model.elaborate()
    s.sim = SimulationTool(s.model)
    s.sim.reset()
    print ""
    s.cycle()

  def cycle(s, extra=None):
    s.sim.cycle()
    s.print_line_trace(extra)
    s.clear()
    s.sim.eval_combinational()

  def print_line_trace(self, extra=None):
    print "{:>3}:".format(
        self.sim
        .ncycles), self.sim.model.line_trace(), "  ", extra if extra else ""

  def reset(s):
    s.sim.reset()


#-------------------------------------------------------------------------
# DefineMethod
#-------------------------------------------------------------------------
@attr.s()
class DefineMethod(object):
  method_name = attr.ib()
  method_call = attr.ib()
  method_rdy = attr.ib(default=None)
  method_clear = attr.ib(default=None)
  arg = attr.ib(default={})
  ret = attr.ib(default={})


#-------------------------------------------------------------------------
# Wrapper
#-------------------------------------------------------------------------


class Wrapper:

  @staticmethod
  def get_wrapper_method_name(method_name, index=-1):
    ''' Return the wrapper method name based on index and count
    '''
    if index >= 0:
      return "{}_{}_".format(method_name, index)
    return method_name

  @staticmethod
  def _get_port(method_name, port_name, index=-1):
    port_name = Interface.mangled_name("", method_name, port_name)
    if index >= 0:
      return "{}[{}]".format(port_name, index)
    return port_name

  @staticmethod
  def _add_method(cls, method_name, method_call, method_rdy):
    """Add method_call and method_rdy to a wrapper cls
    """
    # add method to class
    setattr(method_call, "__name__", method_name + "_call")
    setattr(cls, method_name + "_call", method_call)

    if method_rdy:
      setattr(method_rdy, "__name__", method_name + "_rdy")
      setattr(cls, method_name + "_rdy", method_rdy)

  @staticmethod
  def _validate_input_value(method_name, arg, dtype, value):
    out_of_range_msg = """
  Input arg value out of range.
    - method name : {method_name}
    - arg         : {arg}
    - nbits       : {nbits}
    - min         : 0
    - max         : {max}
    - actual value: {value}
"""
    if not isinstance(dtype, BitStruct) and not (value >= 0 and
                                                 value <= dtype._max):
      raise ValueError(
          out_of_range_msg.format(
              method_name=method_name,
              arg=arg,
              nbits=dtype.nbits,
              max=dtype._max,
              value=value))

  @staticmethod
  def _validate_input(method_name, expected_args_keys, actual_args):
    args_match_msg = """
  Input args do not match with spec.
    - method name  : {method_name}
    - expected args: {expected_args}
    - actual args  : {actual_args}
"""
    if isinstance(actual_args, dict):
      if not set(expected_args_keys) == set(actual_args.keys()):
        raise TypeError(
            args_match_msg.format(
                method_name=method_name,
                expected_args=_list_string(expected_args_keys),
                actual_args=_list_string(actual_args.keys())))
    else:
      error_msg = """
  This method has more than one arg. Please specify by keyword. 
    - method name: {method_name}
    - args       : {args}
"""
      if len(expected_args_keys) != 1:
        raise TypeError(
            error_msg.format(
                method_name=method_name, args=_list_string(expected_args_keys)))

      if len(actual_args) != 1:
        raise TypeError(
            args_match_msg.format(
                method_name=method_name,
                expected_args=expected_args_keys[0],
                actual_args=_list_string(actual_args)))

  @staticmethod
  def _set_input_arg(s, method_name, arg, index, dtype, value):
    if isinstance(dtype, Array):
      assert len(value) == dtype.length
      for i in range(dtype.length):
        Wrapper._validate_input_value(method_name, arg, dtype.Data, value[i])
        port = "{}[{}]".format(Wrapper._get_port(method_name, arg, index), i)
        exec ("s.model.{}.v = {}".format(port, int(value[i]))) in locals()
    else:
      Wrapper._validate_input_value(method_name, arg, dtype, value)
      exec ("s.model.{}.v = {}".format(
          Wrapper._get_port(method_name, arg, index), int(value))) in locals()

  @staticmethod
  def _add_single_method(cls, method_spec, index=-1):
    """Add a single method based on method_spec and index
    index = -1 indicates that this method is not an array
    """
    method_name = method_spec.name

    def method_call(s, *args, **kwargs):
      # assert ready
      if method_spec.rdy:
        exec ("assert s.model.{}, 'Calling method not ready: {}'".format(
            Wrapper._get_port(method_name, "rdy", index),
            method_name)) in locals()

      # set call
      if method_spec.call:
        exec ("s.model.{}.v = 1".format(
            Wrapper._get_port(method_name, "call", index))) in locals()

      # set arg
      if method_spec.args:
        if args:
          Wrapper._validate_input(method_name, method_spec.args.keys(), args)
          arg, dtype = method_spec.args.items()[0]
          Wrapper._set_input_arg(s, method_name, arg, index, dtype, args[0])
        else:
          for key, value in kwargs.items():
            if key[-1] == "_":
              new_key = key[0:-1]
              kwargs[new_key] = kwargs.pop(key)

          Wrapper._validate_input(method_name, method_spec.args.keys(), kwargs)
          for arg, dtype in method_spec.args.iteritems():
            Wrapper._set_input_arg(s, method_name, arg, index, dtype,
                                   kwargs[arg])

      s.sim.eval_combinational()

      # get ret
      ret_values = ReturnValues()
      for ret in method_spec.rets.keys():
        exec ("ret_values.{} = s.model.{}".format(
            ret, Wrapper._get_port(method_name, ret, index))) in locals()
      return ret_values

    def method_rdy(s):
      exec ("rdy = s.model.{}".format(
          Wrapper._get_port(method_name, "rdy", index))) in locals()
      return rdy

    method_name_wrapper = Wrapper.get_wrapper_method_name(
        method_spec.name, index)
    Wrapper._add_method(cls, method_name_wrapper, method_call, method_rdy)

  @staticmethod
  def _add_method_from_spec(cls, method_spec):
    """Add method(s) to wrapper class cls based on method_spec
    """
    method_name = method_spec.name

    if not method_spec.count:
      Wrapper._add_single_method(cls, method_spec)
    else:
      for i in range(method_spec.count):
        Wrapper._add_single_method(cls, method_spec, i)

  @staticmethod
  def _add_clear(cls, methods):
    """Add method that clears call signals every cycle
    """

    def clear(s):
      for name, spec in methods.iteritems():
        if spec.call:
          if spec.count:
            for i in range(spec.count):
              exec ("s.model.{}.v = 0".format(
                  Wrapper._get_port(name, "call", i))) in locals()
          else:
            exec ("s.model.{}.v = 0".format(Wrapper._get_port(
                name, "call"))) in locals()
      for method_clear in cls.methods_clear:
        method_clear(s)
      s.sim.eval_combinational()

    setattr(cls, "clear", clear)

  @staticmethod
  def create_wrapper_class(model, name=None, customized_methods=None):
    """Create wrapper class for rtl model
    """
    for k, v in inspect.getmembers(model):
      if isinstance(v, Interface):
        interface = v

    methods = interface.methods

    if not name:
      name = type(model).__name__ + "Wrapper"

    wrapper_class = type(name, WrapperClass.__bases__,
                         dict(WrapperClass.__dict__))

    for name, method_spec in methods.iteritems():
      Wrapper._add_method_from_spec(wrapper_class, method_spec)

    if customized_methods:
      for method_def in customized_methods:
        method_spec = MethodSpec(
            method_name=method_def.method_name,
            hasrdy=(method_def.method_rdy != None),
            hascall=False,
            islist=False,
            arg=method_def.arg,
            ret=method_def.ret)
        method_specs += [method_spec]
        Wrapper._add_method(wrapper_class, method_spec, method_def.method_call,
                            method_def.method_rdy)
        if method_def.method_clear:
          wrapper_class.methods_clear += [method_def.method_clear]

    Wrapper._add_clear(wrapper_class, methods)
    return wrapper_class

  @staticmethod
  def validate_fl_wrapper_method(spec, target):
    method_error_msg = """
  Method call not implemented!
    - method name: {method_name}
    - args       : {args}
    - rets       : {rets}
"""

    arg_error_msg = """
  Method argument does not match with interface!
    - method name  : {method_name}
    - expected args: {expected_args}
    - actual args  : {actual_args}
"""

    rdy_error_msg = """
  Method rdy not implemented!
    - method name: {method_name}
"""
    method_call = getattr(target, "{}_call".format(spec.name), None)

    if not method_call:
      raise TypeError(
          method_error_msg.format(
              method_name=spec.name,
              args=_list_string(spec.args.keys()),
              rets=_list_string(spec.rets.keys())))

    args, _, _, _ = inspect.getargspec(method_call)

    if set(args[1:]) != set(spec.args.keys()):
      raise TypeError(
          arg_error_msg.format(
              method_name=spec.name,
              expected_args=_list_string(spec.args.keys()),
              actual_args=_list_string(args[1:])))
    if spec.rdy:
      if not hasattr(target, "{}_rdy".format(spec.name)):
        raise TypeError(
            rdy_error_msg.format(
                method_name=spec.name, args=_list_string(spec.args.keys())))


#-------------------------------------------------------------------------
# MethodRule
#-------------------------------------------------------------------------


@attr.s()
class MethodRule(object):
  rtl_method_name = attr.ib()
  fl_method_name = attr.ib()
  arguments = attr.ib()
  precondition = attr.ib()

  def __attrs_post_init__(self):
    self.arguments_strategy = st.fixed_dictionaries(self.arguments)


#-------------------------------------------------------------------------
# add_rule
#-------------------------------------------------------------------------
def add_rule(cls, method_spec):

  name = method_spec.name

  #precondition = getattr(rule_function, PRECONDITION_MARKER, None)
  arguments = cls.argument_strategy(name)
  precondition = cls.precondition(name)
  if not method_spec.count:
    rtl_method_name = Wrapper.get_wrapper_method_name(name)
    rule = MethodRule(
        rtl_method_name=rtl_method_name,
        fl_method_name=name,
        arguments=arguments,
        precondition=precondition)
    cls.add_rule(rule, method_spec.call)
  else:
    for i in range(method_spec.count):
      rtl_method_name = Wrapper.get_wrapper_method_name(name, i)
      rule = MethodRule(
          rtl_method_name=rtl_method_name,
          fl_method_name=name,
          arguments=arguments,
          precondition=precondition)
      cls.add_rule(rule, method_spec.call)


#-------------------------------------------------------------------------
# ArgumentStrategy
#-------------------------------------------------------------------------
class ArgumentStrategy(object):

  def __init__(s, **kwargs):
    s.arguments = kwargs


#-------------------------------------------------------------------------
# Precondition
#-------------------------------------------------------------------------
@attr.s()
class ReferencePrecondition(object):
  precondition = attr.ib()


#-------------------------------------------------------------------------
# precondition
#-------------------------------------------------------------------------
REFERENCE_PRECONDITION_MARKER = u'pymtl-method-based-precondition'


def reference_precondition(precond):
  """Decorator to apply add precondition to an FL model, usually 
    enforces validity of datas

    For example::

        class TestFL:

            @precondition_fl( lambda machine, data: not data[ 'id' ] in machine.reference.snap_shot_free_list )
            def test_method_call( self, id ):
                ...
    """

  def accept(f):
    existing_precondition = getattr(f, REFERENCE_PRECONDITION_MARKER, None)
    if existing_precondition is not None:
      raise InvalidDefinition(
          'A function cannot be used for two distinct preconditions.',
          Settings.default,
      )
    precondition = ReferencePrecondition(precondition=precond)

    @proxies(f)
    def precondition_wrapper(*args, **kwargs):
      return f(*args, **kwargs)

    setattr(precondition_wrapper, REFERENCE_PRECONDITION_MARKER, precondition)
    return precondition_wrapper

  return accept


class MethodStrategy:
  pass


#-------------------------------------------------------------------------
# CompareTest
#-------------------------------------------------------------------------
class CompareTest(TestStateMachine):
  sim = None
  reference = None

  def __init__(self):
    TestStateMachine.__init__(self)
    self.sim.reset()
    self.reference.reset()
    self.sim.cycle()
    if hasattr(self.reference, 'cycle'):
      self.reference.cycle()


#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------
def create_test_state_machine(model, reference, customized_methods=None):
  WrapperClass = Wrapper.create_wrapper_class(
      model, customized_methods=customized_methods)

  sim = WrapperClass(model)

  Test = type(
      type(model).__name__ + "TestStateMachine", CompareTest.__bases__,
      dict(CompareTest.__dict__))

  Test.interface = None

  for k, v in inspect.getmembers(reference):
    if isinstance(v, Interface):
      Test.interface = v
      Test.interface.require_fl_methods(reference)

    precondition = getattr(v, REFERENCE_PRECONDITION_MARKER, None)

    if precondition != None:
      Test.add_precondition(method_name_fl, precondition.precondition)

    if isinstance(v, MethodStrategy):
      for method, strategy in inspect.getmembers(v):
        if isinstance(strategy, ArgumentStrategy):
          Test.add_argument_strategy(method, strategy.arguments)

  if not Test.interface:
    raise RunMethodTestError("Get rtl model with no interface specified! ")
  # make sure that all method arguments have strategy specified
  error_msg = """
  Found argument with no strategy specified!
    - method name : {method_name}
    - arg         : {arg} 
"""
  for name, spec in Test.interface.methods.iteritems():
    strategies = Test.argument_strategy(name)
    for arg, dtype in spec.args.iteritems():
      if not strategies.has_key(arg):
        if isinstance(dtype, BitStruct):
          strategies[arg] = bitstruct_strategy(dtype)
        elif isinstance(dtype, Bits):
          strategies[arg] = bits_strategy(dtype.nbits)
        else:
          raise RunMethodTestError(error_msg.format(method_name=name, arg=arg))

  # add rule
  for name, spec in Test.interface.methods.iteritems():
    add_rule(Test, spec)

  Test.sim = sim
  Test.reference = reference

  return Test


#-------------------------------------------------------------------------
# generate_methods_from_model
#-------------------------------------------------------------------------
def generate_methods_from_model(model):
  #method_specs = inspect_methods( model )

  # get unique methods
  method_spec_dict = {}
  for name, spec in s.methods.iteritems():
    method_spec_dict[spec.method_name] = spec

  for method_name, spec in method_spec_dict.items():
    arguments = _list_string(['s'] + spec.arg.keys())
    print "  def {}_call( {} ):".format(method_name, arguments)
    if spec.hasrdy:
      print "    assert s.{}_rdy()".format(method_name)
    return_list = ["{}=0".format(ret) for ret in spec.ret.keys()]
    if return_list:
      print "    return ReturnValues( {} )".format(_list_string(return_list))
    else:
      print "    pass"
    print ""

    if spec.hasrdy:
      print "  def {}_rdy( s ):".format(method_name)
      print "    return True"
      print ""

  print "  def reset( s ):"
  print "    pass"


#-------------------------------------------------------------------------
# bits_strategy
#-------------------------------------------------------------------------
def bits_strategy(nbits):
  return st.integers(min_value=0, max_value=Bits(nbits)._max)


#-------------------------------------------------------------------------
# get_bitstruct_strategy
#-------------------------------------------------------------------------
def bitstruct_strategy(bitstruct, **kwargs):

  @st.composite
  def strategy(draw):
    new_bitstruct = create_test_bitstruct(bitstruct)()
    for name, slice_ in type(bitstruct)._bitfields.iteritems():
      if not name in kwargs.keys():
        data = draw(bits_strategy(slice_.stop - slice_.start))
      else:
        data = draw(kwargs[name])
      exec ("new_bitstruct.{} = data".format(name)) in locals()
    return new_bitstruct

  return strategy()


#-------------------------------------------------------------------------
# ReturnValues
#-------------------------------------------------------------------------


class ReturnValues:

  def __init__(s, **kwargs):
    for k, v in kwargs.items():
      setattr(s, k, v)


def run_state_machine(state_machine_factory):
  state_machine_factory.TestCase.settings = settings(
      max_examples=50, deadline=None, verbosity=Verbosity.verbose)
  run_state_machine_as_test(state_machine_factory)


def bitstruct_detail(bitstruct):
  bitfields = []
  for k, v in bitstruct._bitfields.iteritems():
    bitfields += ["{}: {}".format(k, bitstruct[v.start:v.stop])]
  return "( " + _list_string(bitfields) + " )"
