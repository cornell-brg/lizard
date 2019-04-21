import copy
import inspect
import hypothesis.strategies as st
from pymtl import *
from hypothesis.stateful import *
from hypothesis import settings, given
from sets import Set
from util.rtl.interface import Interface
from util.rtl.types import Array
from model.wrapper import wrap_to_cl
from model.hardware_model import NotReady, Result
from util.pretty_print import list_string_value, list_string
from model.translate import translate
import copy

debug = True


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
    if n > 0:
      remaining_rules = [i for i in range(0, n)]
      num_rules = cu.integer_range(data, 1, n)
      for _ in range(num_rules):
        i = cu.integer_range(data, 0, len(remaining_rules) - 1)
        rule_to_fire += [self.condition_rules[remaining_rules[i]]]
        del remaining_rules[i]

    rule_to_fire.sort(
      key=lambda rule: (
        self.machine.interface.methods.keys().index( rule.method_name ),
        rule.index,
        rule.method_name,
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
    self.__rtl_pending = {}
    self.__fl_pending = {}

  def _sim_cycle(self, method_line_trace=""):
    self.sim.cycle()
    print "{:>3}: {}  {}".format(self.sim.sim.ncycles,
                                 self.sim.model.line_trace(), method_line_trace)

  def _error_line_trace(self, method_line_trace, error_msg):
    self._sim_cycle(method_line_trace)
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
            model_ret=list_string(m_ret_names),
            reference_ret="")
        self._error_line_trace(method_line_trace, error_msg)
      else:
        return

    r_ret_names = set(sorted(r_ret.keys()))
    if r_ret_names != m_ret_names:
      error_msg = type_error_msg.format(
          method_name=method_name,
          model_ret=list_string(m_ret_names),
          reference_ret=list_string(r_ret_names))
      self._error_line_trace(method_line_trace, error_msg)

  def compare_result(self, m_result, r_result, method_name, arg,
                     method_line_trace):
    r_result = r_result._data
    m_result = m_result._data

    #self._validate_result(m_ret_names, r_result, method_name, arg,
    #                      method_line_trace)

    value_error_msg = """
   test state machine received an incorrect value!
    - method name    : {method_name}
    - arguments      : {arg}
    - ret name       : {ret_name}
    - expected value : {expected_msg}
    - actual value   : {actual_msg}
  """

    for k in r_result.keys():
      if r_result[k] != '?' and not r_result[k] == m_result[k]:
        m_ret_names = set(sorted(m_result.keys()))
        m_result_list = [value for (key, value) in sorted(m_result.items())]
        r_result_list = [value for (key, value) in sorted(r_result.items())]
        error_msg = value_error_msg.format(
            method_name=method_name,
            arg=arg,
            ret_name=list_string(m_ret_names),
            expected_msg=list_string_value(r_result_list),
            actual_msg=list_string_value(m_result_list))
        self._error_line_trace(method_line_trace, error_msg)

  def steps(self):
    return self.__rules_strategy

  def _call_func(s, model, name, data, index=-1):
    func = getattr(model, name)
    if index < 0:
      return func(**data)
    return func[index](**data)

  def execute_step(self, step):
    # store result of sim and reference
    s_results = []
    r_results = []
    method_names = []
    data_list = []

    method_line_trace = []
    # go though all rules for this step
    rule_to_fire = {}
    for ruledata in step:
      rule, data = ruledata
      data = dict(data)
      rule_to_fire[rule.method_name] = (rule, data)

    for name, (data, rule, _) in self.__rtl_pending.iteritems():
      rule_to_fire[rule.method_name] = (rule, data)

    rule_to_fire = rule_to_fire.values()

    rule_to_fire.sort(
      key=lambda ruledata: (
        self.interface.methods.keys().index( ruledata[0].method_name ),
        ruledata[0].index,
        ruledata[0].method_name,
      )
    )

    for (rule, data) in rule_to_fire:
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
      method_name = rule.method_name
      index = rule.index

      # First check if methods are ready
      if self.release_cycle_accuracy:
        if self.__rtl_pending.has_key(method_name):
          assert not self.__fl_pending.has_key(method_name)
          data, rule, r_result = self.__rtl_pending[method_name]
          index = rule.index
          s_result = self._call_func(self.sim, method_name, data, index)
          del self.__rtl_pending[method_name]
        elif self.__fl_pending.has_key(method_name):
          assert not self.__rtl_pending.has_key(method_name)
          data, rule, s_result = self.__fl_pending[method_name]
          index = rule.index
          r_result = self._call_func(self.reference, method_name, data, index)
          del self.__fl_pending[method_name]
        else:
          s_result = self._call_func(self.sim, method_name, data, index)
          r_result = self._call_func(self.reference, method_name, data)

        if isinstance(s_result, NotReady):
          if not isinstance(r_result, NotReady):
            self.__rtl_pending[method_name] = (data, rule, r_result)
            continue
          continue

        if isinstance(r_result, NotReady):
          self.__fl_pending[method_name] = (data, rule, s_result)
          continue

      else:
        s_result = self._call_func(self.sim, method_name, data, index)
        r_result = self._call_func(self.reference, method_name, data)

        if isinstance(s_result, NotReady):
          if not isinstance(r_result, NotReady):
            raise RunMethodTestError(
                "Reference model is rdy but RTL model is not: {}".format(
                    method_name))
          continue

        if isinstance(r_result, NotReady):
          if self.release_cycle_accuracy:
            self.__fl_pending_data[method_name] = data
            continue
          raise RunMethodTestError(
              "RTL model is rdy but Reference is not: {}".format(method_name))

      # Method ready, add to result list
      method_names += [method_name]

      # If in debug mode, print out all the methods called
      if debug:
        argument_string = []
        for k, v in data.items():
          if isinstance(v, BitStruct):
            v = bitstruct_detail(v)
          argument_string += ["{}={}".format(k, v)]
        index_string = "[{}]".format(index) if index >= 0 else ""
        method_line_trace += [
            "{}{}( {} )".format(method_name, index_string,
                                list_string(argument_string))
            if argument_string else "{}{}()".format(method_name, index_string)
        ]

      # Add to result list
      s_results += [s_result]
      r_results += [r_result]

    method_line_trace = ",  ".join(method_line_trace)

    # Compare results
    for s_result, r_result, method, data in zip(s_results, r_results,
                                                method_names, data_list):
      self.compare_result(s_result, r_result, method, data, method_line_trace)

    self._sim_cycle(method_line_trace)
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
# MethodRule
#-------------------------------------------------------------------------


@attr.s()
class MethodRule(object):
  method_name = attr.ib()
  arguments = attr.ib()
  precondition = attr.ib()
  index = attr.ib(default=-1)

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
  if method_spec.count == None:
    rule = MethodRule(
        method_name=name, arguments=arguments, precondition=precondition)
    cls.add_rule(rule, method_spec.call)
  else:
    for i in range(method_spec.count):
      rule = MethodRule(
          method_name=name,
          arguments=arguments,
          precondition=precondition,
          index=i)
      cls.add_rule(rule, method_spec.call)


#-------------------------------------------------------------------------
# ArgumentStrategy
#-------------------------------------------------------------------------
class ArgumentStrategy(object):

  def __init__(s, **kwargs):
    s.arguments = kwargs

  @staticmethod
  def bits_strategy(nbits):
    return st.integers(min_value=0, max_value=Bits(nbits)._max)

  @staticmethod
  def value_strategy(range_value=None, start=0):
    return st.integers(
        min_value=start, max_value=range_value - 1 if range_value else None)

  @staticmethod
  def bitstruct_strategy(bitstruct, **kwargs):

    @st.composite
    def strategy(draw):
      new_bitstruct = bitstruct()
      for name, slice_ in type(bitstruct)._bitfields.iteritems():
        if not name in kwargs.keys():
          data = draw(
              ArgumentStrategy.bits_strategy(slice_.stop - slice_.start))
        else:
          data = draw(kwargs[name])
        exec ("new_bitstruct.{} = data".format(name)) in locals()
      return new_bitstruct

    return strategy()

  @staticmethod
  def bitstype_strategy(dtype):

    if isinstance(dtype, BitStruct):
      return ArgumentStrategy.bitstruct_strategy(dtype)
    elif isinstance(dtype, Bits):
      return ArgumentStrategy.bits_strategy(dtype.nbits)
    raise TypeError("No supported bitstype strategy for {}".format(type(dtype)))

  @staticmethod
  def array_strategy(dtype):
    if not isinstance(dtype, Array):
      raise TypeError("No supported array strategy for {}".format(type(dtype)))
    return st.lists(
        ArgumentStrategy.bitstype_strategy(dtype.Data),
        min_size=dtype.length,
        max_size=dtype.length)

  @staticmethod
  def get_strategy_from_type(dtype):
    if isinstance(dtype, Array):
      return ArgumentStrategy.array_strategy(dtype)
    if isinstance(dtype, Bits) or isinstance(dtype, BitStruct):
      return ArgumentStrategy.bitstype_strategy(dtype)
    return None


#-------------------------------------------------------------------------
# ArgumentDependency
#-------------------------------------------------------------------------
@attr.s()
class ArgumentDependency(object):
  method = attr.ib()
  arg = attr.ib()
  strategy_func = attr.ib()


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
# TestModel
#-------------------------------------------------------------------------
class TestModel(TestStateMachine):
  sim = None
  reference = None

  def __init__(self):
    TestStateMachine.__init__(self)
    self.sim.reset()
    self.reference.reset()
    self._sim_cycle()
    self.reference.cycle()

  @staticmethod
  def _create_test_state_machine(rtl_class,
                                 reference_class,
                                 parameters,
                                 argument_strategy={},
                                 translate_model=False,
                                 release_cycle_accuracy=False):

    if isinstance(parameters, dict):
      parameters_string = "_".join(
          [str(parameter) for parameter in parameters.values()])
      model = rtl_class(**parameters)
      reference = reference_class(**parameters)
    else:
      if not isinstance(parameters, tuple):
        parameters = (parameters,)
      parameters_string = "_".join([str(parameter) for parameter in parameters])
      model = rtl_class(*parameters)
      reference = reference_class(*parameters)
    if translate_model:
      model = translate(model)
    model.vcd_file = "machine.vcd"
    sim = wrap_to_cl(model)

    Test = type(
        type(model).__name__ + "TestStateMachine_" + parameters_string,
        TestModel.__bases__, dict(TestModel.__dict__))

    Test.interface = None
    if type(model.interface) != type(reference.interface):
      raise RunMethodTestError("Model and reference interface don't match!")

    Test.interface = model.interface

    for k, v in inspect.getmembers(reference):

      precondition = getattr(v, REFERENCE_PRECONDITION_MARKER, None)

      if precondition != None:
        Test.add_precondition(method_name_fl, precondition.precondition)

      if isinstance(v, MethodStrategy):
        for method, strategy in inspect.getmembers(v):
          if isinstance(strategy, ArgumentStrategy):
            Test.add_argument_strategy(method, strategy.arguments)

    for method, arguments in argument_strategy.iteritems():
      if isinstance(arguments, ArgumentStrategy):
        arguments = arguments.arguments
      Test.add_argument_strategy(method, arguments)

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
          strategies[arg] = ArgumentStrategy.get_strategy_from_type(dtype)
          if not strategies[arg]:
            raise RunMethodTestError(
                error_msg.format(method_name=name, arg=arg))

    # add rule
    for name, spec in Test.interface.methods.iteritems():
      add_rule(Test, spec)

    Test.sim = sim
    Test.reference = reference
    Test.release_cycle_accuracy = release_cycle_accuracy

    return Test

  @staticmethod
  def _run_state_machine(state_machine_factory):
    state_machine_factory.TestCase.settings = settings(
        max_examples=50, deadline=None, verbosity=Verbosity.verbose)
    run_state_machine_as_test(state_machine_factory)


#-------------------------------------------------------------------------
# run_test_state_machine
#-------------------------------------------------------------------------
def run_test_state_machine(rtl_class,
                           reference_class,
                           parameters,
                           translate_model=False,
                           argument_strategy={},
                           release_cycle_accuracy=False):
  state_machine_factory = TestModel._create_test_state_machine(
      rtl_class,
      reference_class,
      parameters,
      translate_model=translate_model,
      argument_strategy=argument_strategy,
      release_cycle_accuracy=release_cycle_accuracy)
  TestModel._run_state_machine(state_machine_factory)


#-------------------------------------------------------------------------
# init_strategy
#-------------------------------------------------------------------------
INIT_STRATEGY_MARKER = u'pymtl-method-based-init-strategy'


def init_strategy(**kwargs):

  def accept(f):
    arg_list = kwargs

    @st.composite
    def parameter_strategy(draw):
      parameters = {}
      for key, arg in kwargs.iteritems():
        # Type specified
        if arg is Bits:
          nbits = draw(st.integers(min_value=1, max_value=64))
          parameters[key] = Bits(nbits)
        elif arg is int:
          value = draw(st.integers(min_value=1, max_value=64))
          parameters[key] = value
        elif arg is bool:
          value = draw(st.booleans())
          parameters[key] = value
        elif isinstance(arg, SearchStrategy):
          value = draw(arg)
          parameters[key] = value
        elif isinstance(arg, int) or isinstance(arg, Bits) or isinstance(
            arg, bool):
          parameters[key] = arg
        elif callable(arg):
          args, _, _, _ = inspect.getargspec(arg)
          arg_dict = {}
          parameter_keys = parameters.keys()
          for a in args:
            if not a in parameter_keys:
              raise ValueError("""
  Init parameter strategy can only depend on parameters defined previously!
    - defined parameters: {parameter_keys}
    - found: {parameter}
""".format(parameter_keys=list_string(parameter_keys), parameter=a))
            arg_dict[a] = parameters[a]
          value = draw(arg(**arg_dict))
          parameters[key] = value
        else:
          raise TypeError("Unsupported parameter type")

      return parameters

    setattr(f, INIT_STRATEGY_MARKER, parameter_strategy)
    return f

  return accept


#-------------------------------------------------------------------------
# run_parameterized_test_state_machine
#-------------------------------------------------------------------------


def run_parameterized_test_state_machine(rtl_class,
                                         reference_class,
                                         method_strategy_class,
                                         translate_model=False,
                                         release_cycle_accuracy=False):

  parameter_strategy = getattr(method_strategy_class.__init__,
                               INIT_STRATEGY_MARKER, None)

  @settings(deadline=None, max_examples=10)
  @given(parameter_strategy(), st.data())
  def run_multiple_state_machines(parameters, data):
    arguments = {}

    init_args, _, _, default = inspect.getargspec(rtl_class.__init__)
    if default is None:
      default = []
    init_args = init_args[1:len(init_args) - len(default)]
    if set(init_args) - set(parameters.keys()):
      raise ValueError("""
  Found arg in rtl model __init__ args not int init_strategy!
    - init_strategy: {strategy_func_arg}
    - rtl __init__ : {init_args}
""".format(
          strategy_func_arg=list_string(parameters.keys()),
          init_args=list_string(init_args)))

    args, _, _, _ = inspect.getargspec(method_strategy_class.__init__)
    args = args[1:]
    if set(init_args) - set(args):
      raise ValueError("""
  Found arg in rtl model __init__ args not int method_strategy class __init__!
    - method_strategy: {strategy_func_arg}
    - rtl model      : {init_args}
""".format(
          strategy_func_arg=list_string(args),
          init_args=list_string(init_args)))
    method_strategy = method_strategy_class(**parameters)

    for k, v in inspect.getmembers(method_strategy):
      if isinstance(v, ArgumentStrategy):
        target = arguments.setdefault(k, {})
        for arg_name, strategy in v.arguments.iteritems():
          target[arg_name] = st.deferred(lambda s=strategy: s)
    state_machine_factory = TestModel._create_test_state_machine(
        rtl_class,
        reference_class,
        parameters,
        translate_model=translate_model,
        argument_strategy=arguments,
        release_cycle_accuracy=release_cycle_accuracy)
    TestModel._run_state_machine(state_machine_factory)

  run_multiple_state_machines()


#-------------------------------------------------------------------------
# bitstruct_detail
#-------------------------------------------------------------------------
def bitstruct_detail(bitstruct):
  bitfields = []
  for k, v in bitstruct._bitfields.iteritems():
    bitfields += ["{}: {}".format(k, bitstruct[v.start:v.stop])]
  return "( " + list_string(bitfields) + " )"
