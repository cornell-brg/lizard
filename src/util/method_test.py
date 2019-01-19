import copy
import inspect
import hypothesis.strategies as st
from pymtl import *
from hypothesis.stateful import *
from hypothesis.vendor.pretty import CUnicodeIO, RepresentationPrinter
from sets import Set
from util.rtl.method import InMethodCallPortBundle

debug = True


#-------------------------------------------------------------------------
# MethodBasedRuleStrategy
#-------------------------------------------------------------------------
def get_order( cls, method_name ):
  method_name_fl = cls.method_name_fl( method_name )
  order = cls.order()
  if not method_name_fl in order:
    return len( order )
  return order.index( method_name_fl )


class MethodBasedRuleStrategy( SearchStrategy ):

  def __init__( self, machine ):
    SearchStrategy.__init__( self )
    self.machine = machine
    self.rules = list( machine.rules() )

    order = self.machine.order()

    self.rules.sort(
      key=lambda rule: (
        get_order( self.machine, rule.function.__name__ ),
        rule.function.__name__,
      )
    )

  def do_draw( self, data ):
    # This strategy draw a randomly selected number of rules and do not care about
    # validity. In execute_step(step), only valid rules will be fired. We do this to
    # test possible dependencies - some rules are not valid in the first place become
    # valid if some other rules fire in the same cycle
    n = len( self.rules )
    rule_to_fire = []
    remaining_rules = [ i for i in range( 0, n ) ]
    num_rules = cu.integer_range( data, 1, n - 1 )
    for _ in range( num_rules ):
      i = cu.integer_range( data, 0, len( remaining_rules ) - 1 )
      rule_to_fire += [ self.rules[ remaining_rules[ i ] ] ]
      del remaining_rules[ i ]

    order = self.machine.order()
    rule_to_fire.sort(
      key=lambda rule: (
        get_order( self.machine, rule.function.__name__ ),
        rule.function.__name__,
      )
    )
    if rule_to_fire:
      return [( rule, data.draw( rule.arguments_strategy ) )
              for rule in rule_to_fire ]


#-------------------------------------------------------------------------
# TestStateMachine
#-------------------------------------------------------------------------
class RunMethodTestError( Exception ):
  pass


class TestStateMachine( RuleBasedStateMachine ):
  __argument_strategies = {}
  __preconditions = {}
  __method_name_fl = {}
  __order = {}

  def __init__( self ):
    super( TestStateMachine, self ).__init__()
    self.__rules_strategy = MethodBasedRuleStrategy( self )
    self.__stream = CUnicodeIO()
    self.__printer = RepresentationPrinter( self.__stream )

  def compare_result( self, m_result, r_result, method_name, arg,
                      method_line_trace ):
    if isinstance( r_result, ReturnValues ):
      r_result = r_result.__dict__

    if r_result:
      if isinstance( r_result, dict ):
        r_ret_names = set( sorted( r_result.keys() ) )
        m_ret_names = set( sorted( m_result.keys() ) )
        if r_ret_names != m_ret_names:
          error_msg = """
   Reference and model have mismatched returns!
    - method name    : {method_name}
    - model ret      : {model_ret}
    - reference ret  : {reference_ret}
  """
          error_msg = error_msg.format(
              method_name=method_name,
              model_ret=", ".join( m_ret_names ),
              reference_ret=", ".join( r_ret_names ) )
          self.sim.cycle( method_line_trace )
          print "========================== error =========================="
          raise RunMethodTestError( error_msg )
        for k in r_result.keys():
          if r_result[ k ] != '?' and not m_result[ k ] == r_result[ k ]:
            error_msg = """
   test state machine received an incorrect value!
    - method name    : {method_name}
    - arguments      : {arg}
    - ret name       : {ret_name}
    - expected value : {expected_msg}
    - actual value   : {actual_msg}
  """
            error_msg = error_msg.format(
                method_name=method_name,
                arg=arg,
                ret_name=k,
                expected_msg=r_result[ k ],
                actual_msg=m_result[ k ] )
            self.sim.cycle( method_line_trace )
            print "========================== error =========================="
            raise RunMethodTestError( error_msg )
      else:
        assert isinstance( r_result, int ) or isinstance( r_result, tuple )
        # assume that results are in alphabetical order
        m_result_list = [
            value for ( key, value ) in sorted( m_result.items() )
        ]
        r_result_list = [ r_result ] if isinstance( r_result,
                                                    int ) else list( r_result )
        for m_result_value, r_result_value in zip( m_result_list,
                                                   r_result_list ):
          if r_result_value != '?' and m_result_value != r_result:
            error_msg = """
   test state machine received an incorrect value!
    - method name    : {method_name}
    - arguments      : {arg}
    - ret name       : {ret_name}
    - expected value : {expected_msg}
    - actual value   : {actual_msg}
  """
            error_msg = error_msg.format(
                method_name=method_name,
                arg=arg,
                ret_name=', '.join( sorted( m_result.keys() ) ),
                expected_msg=', '.join(
                    [ str( result ) for result in r_result_list ] ),
                actual_msg=', '.join(
                    [ str( result ) for result in m_result_list ] ) )
            self.sim.cycle( method_line_trace )
            print "========================== error =========================="
            raise RunMethodTestError( error_msg )

  def steps( self ):
    # Pick initialize rules first
    if self._initialize_rules_to_run:
      return one_of([
          tuples( just( rule ), fixed_dictionaries( rule.arguments ) )
          for rule in self._initialize_rules_to_run
      ] )
    return self.__rules_strategy

  def execute_step( self, step ):
    # store result of sim and reference
    s_results = []
    r_results = []
    method_names = []
    data_list = []

    method_line_trace = []
    # go though all rules for this step
    for ruledata in step:
      rule, data = ruledata
      data = dict( data )

      # For dependency reason we do allow rules invalid in the first place
      # to be added to step.
      # See MethodBasedRuleStrategy for more
      if not self.is_valid( rule, data ):
        continue

      data_list += [ data ]
      for k, v in list( data.items() ):
        if isinstance( v, VarReference ):
          data[ k ] = self.names_to_values[ v.name ]
      result = rule.function( self, **data )

      # For method based interface rules, call rdy ones only
      name = rule.function.__name__
      method_names += [ name ]
      sim_class_members = self.sim.__class__.__dict__
      reference_class_members = self.reference.__class__.__dict__

      if name + "_call" in sim_class_members.keys():
        hasrdy = self.sim.methods_fl[ name ].hasrdy
        rdy = False
        if hasrdy:
          if sim_class_members[ name + "_rdy" ]( self.sim ):
            assert reference_class_members[ self.method_name_fl( name ) +
                                            "_rdy" ](
                                                self.reference )
            rdy = True
        if not hasrdy or rdy:
          if debug:
            argument_string = []
            for k, v in data.items():
              argument_string += [ "{}={}".format( k, v ) ]
            method_line_trace += [
                "{}( {} )".format( name, ", ".join( argument_string ) )
                if argument_string else "{}()".format( name )
            ]
          s_results += [
              sim_class_members[ name + "_call" ]( self.sim, **data )
          ]
          r_results += [
              reference_class_members[ self.method_name_fl( name ) + "_call" ](
                  self.reference, **data )
          ]

      if self._initialize_rules_to_run:
        self._initialize_rules_to_run.remove( rule )

    method_line_trace = ",  ".join( method_line_trace )
    for s_result, r_result, method, data in zip( s_results, r_results,
                                                 method_names, data_list ):
      self.compare_result( s_result, r_result, method, data, method_line_trace )

    self.sim.cycle( method_line_trace )
    if hasattr( self.reference, 'cycle' ):
      self.reference.cycle()

  def print_step( self, step ):
    pass

  def is_valid( self, rule, data ):
    if rule.precondition and not rule.precondition( self, data ):
      return False
    for b in rule.bundles:
      bundle = self.bundle( b.name )
      if not bundle:
        return False
    return True

  @classmethod
  def add_argument_strategy( cls, method, arguments ):
    target = cls.__argument_strategies.setdefault( cls, {} )
    if target.has_key( method ):
      error_msg = """
      A method cannot have two distince strategies. 
        method_name : {method_name}
      """.format( method_name=method )
      raise InvalidDefinition( error_msg )
    target[ method ] = arguments

  @classmethod
  def argument_strategy( cls, method ):
    target = cls.__argument_strategies.setdefault( cls, {} )
    return target.setdefault( method, {} )

  @classmethod
  def add_precondition( cls, method, precondition ):
    target = cls.__preconditions.setdefault( cls, {} )
    target[ method ] = precondition

  @classmethod
  def precondition( cls, method ):
    target = cls.__preconditions.setdefault( cls, {} )
    return target.setdefault( method, None )

  @classmethod
  def add_method_name_fl( cls, method, method_name_fl ):
    target = cls.__method_name_fl.setdefault( cls, {} )
    target[ method ] = method_name_fl

  @classmethod
  def method_name_fl( cls, method ):
    target = cls.__method_name_fl.setdefault( cls, {} )
    return target.setdefault( method, method )

  @classmethod
  def set_order( cls, order ):
    print cls.__order
    cls.__order[ cls ] = order

  @classmethod
  def order( cls ):
    target = cls.__order.setdefault( cls, [] )
    return target


#-------------------------------------------------------------------------
# WrapperClass
#-------------------------------------------------------------------------
class WrapperClass:
  methods = {}
  methods_fl = {}
  methods_clear = []

  def __init__( s, model ):
    s.model = model
    s.model.elaborate()
    s.sim = SimulationTool( s.model )
    s.sim.reset()
    print ""
    s.cycle()

  def cycle( s, extra=None ):
    s.sim.cycle()
    s.print_line_trace( extra )
    s.clear()
    s.sim.eval_combinational()

  def print_line_trace( self, extra=None ):
    print "{:>3}:".format(
        self.sim
        .ncycles ), self.sim.model.line_trace(), "  ", extra if extra else ""

  def reset( s ):
    s.sim.reset()


#-------------------------------------------------------------------------
# MethodSpec
#-------------------------------------------------------------------------
@attr.s()
class MethodSpec( object ):
  method_name = attr.ib()
  hasrdy = attr.ib()
  hascall = attr.ib()
  islist = attr.ib( default=False )
  index = attr.ib( default=None )
  arg = attr.ib( default={} )
  ret = attr.ib( default={} )


#-------------------------------------------------------------------------
# DefineMethod
#-------------------------------------------------------------------------
@attr.s()
class DefineMethod( object ):
  method_name = attr.ib()
  method_call = attr.ib()
  method_rdy = attr.ib( default=None )
  method_clear = attr.ib( default=None )
  arg = attr.ib( default={} )
  ret = attr.ib( default={} )


#-------------------------------------------------------------------------
# inspect_methods
#-------------------------------------------------------------------------


def inspect_methods( model ):
  ''' 
  Inspect the model and return a list of method_spec that is used 
  for generating *_call and *_rdy methods in wrapper class
  
  - example method_spec: 
  MethodSpec( method_name="read_ports", islist=True, index=0, arg={ "areg": Bits(1) }, ret=[ "preg" ], hasrdy=False, hascall=True )
  
  By default, *_call methods created by this function 
  take in arguments in alphabetical order
  '''
  method_specs = []

  def get_method_spec( method_name, port_bundle, islist=False, index=None ):
    # get rdy
    hasrdy = hasattr( port_bundle, 'rdy' )
    hascall = hasattr( port_bundle, 'call' )

    method_spec = MethodSpec(
        method_name=method_name,
        hasrdy=hasrdy,
        hascall=hascall,
        islist=islist,
        index=index )

    # get arg and ret
    arg = {}
    ret = {}
    for port in port_bundle._ports:
      name = port.name
      dtype = port.dtype
      if type( port ) == InPort:
        if name != 'call':
          arg[ name ] = dtype
      else:
        if name != 'rdy':
          ret[ name ] = dtype
    method_spec.arg = arg
    method_spec.ret = ret

    return method_spec

  for k, v in inspect.getmembers( model ):
    # single method port bundle
    if isinstance( v, InMethodCallPortBundle ):
      method_spec = get_method_spec( k, v )
      method_specs += [ method_spec ]

    # method port bundle list
    if isinstance( v, list ):
      # inspect each element
      for i in range( len( v ) ):
        if k[ 0 ] != '_' and isinstance( v[ i ], InMethodCallPortBundle ):
          method_spec = get_method_spec(
              method_name=k, port_bundle=v[ i ], islist=True, index=i )
          method_specs += [ method_spec ]

  return method_specs


#-------------------------------------------------------------------------
# add_method
#-------------------------------------------------------------------------
def add_method( cls, method_spec, method_call, method_rdy ):
  method_name = method_spec.method_name
  if method_spec.islist:
    name = "{}_{}_".format( method_name, method_spec.index )
    method_name = "{}[{}]".format( method_name, method_spec.index )
  else:
    name = method_name

  cls.methods[ method_name ] = method_spec
  cls.methods_fl[ name ] = method_spec

  # add method to class
  setattr( method_call, "__name__", name + "_call" )
  setattr( cls, name + "_call", method_call )

  if method_spec.hasrdy:
    setattr( method_rdy, "__name__", name + "_rdy" )
    setattr( cls, name + "_rdy", method_rdy )


#-------------------------------------------------------------------------
# add_method_from_spec
#-------------------------------------------------------------------------
def add_method_from_spec( cls, method_spec ):
  method_name = method_spec.method_name
  if method_spec.islist:
    name = "{}_{}_".format( method_name, method_spec.index )
    method_name = "{}[{}]".format( method_name, method_spec.index )
  else:
    name = method_name

  def method_call( s, *args, **kwargs ):
    # assert ready
    if method_spec.hasrdy:
      exec ( "assert s.{}_rdy()".format( name ) ) in locals()

    # set call
    if method_spec.hascall:
      exec ( "s.model.{}.call.value = 1".format( method_name ) ) in locals()

    # set arg
    if method_spec.arg:
      index = 0
      args_list = method_spec.arg.keys()
      args_list.sort()

      for arg in args_list:
        if args and kwargs:
          raise RunMethodTestError(
              """Mixture of keyworded and non-keyworded arguments is not supported
for {}_call method. Use keywords, or pass in arguments by alphabetical order. 
""".format( name ) )
        if not len( args ) == len( args_list ) and \
          not len( kwargs ) == len( args_list ):

          raise RunMethodTestError()
        if args:
          exec ( "s.model.{}.{}.value = args[ {} ]".format(
              method_name, arg, index ) ) in locals()
          index += 1
        else:
          exec ( "s.model.{}.{}.value = kwargs[ '{}' ]".format(
              method_name, arg, arg ) ) in locals()

    s.sim.eval_combinational()

    # get ret
    ret_values = {}
    for ret in method_spec.ret.keys():
      exec ( "ret_values[ ret ] = s.model.{}.{}".format( method_name,
                                                         ret ) ) in locals()
    return ret_values

  def method_rdy( s ):
    exec ( "rdy = s.model.{}.rdy".format( method_name ) ) in locals()
    return rdy

  add_method( cls, method_spec, method_call, method_rdy )


#-------------------------------------------------------------------------
# add_clear
#-------------------------------------------------------------------------
def add_clear( cls ):

  def clear( s ):
    for method, spec in cls.methods.items():
      if spec.hascall:
        exec ( "s.model.{}.call.value = 0".format( method ) ) in locals()
    for method_clear in cls.methods_clear:
      method_clear( s )
    s.sim.eval_combinational()

  setattr( cls, "clear", clear )


#-------------------------------------------------------------------------
# create_wrapper_class
#-------------------------------------------------------------------------
def create_wrapper_class( model,
                          name=None,
                          method_specs=None,
                          customized_methods=None ):
  if not method_specs:
    method_specs = inspect_methods( model )

  if not name:
    name = type( model ).__name__ + "Wrapper"

  wrapper_class = type( name, WrapperClass.__bases__,
                        dict( WrapperClass.__dict__ ) )

  for method_spec in method_specs:
    add_method_from_spec( wrapper_class, method_spec )

  if customized_methods:
    for method_def in customized_methods:
      method_spec = MethodSpec(
          method_name=method_def.method_name,
          hasrdy=( method_def.method_rdy != None ),
          hascall=False,
          islist=False,
          arg=method_def.arg,
          ret=method_def.ret )
      method_specs += [ method_spec ]
      add_method( wrapper_class, method_spec, method_def.method_call,
                  method_def.method_rdy )
      if method_def.method_clear:
        wrapper_class.methods_clear += [ method_def.method_clear ]

  add_clear( wrapper_class )
  return wrapper_class, method_specs


#-------------------------------------------------------------------------
# add_rule
#-------------------------------------------------------------------------
def add_rule( cls, method_spec ):
  method_name_fl = method_spec.method_name
  if method_spec.islist:
    name = "{}_{}_".format( method_name_fl, method_spec.index )
    cls.add_method_name_fl( name, method_name_fl )
  else:
    name = method_name_fl

  def rule_function(*args, **kwargs ):
    pass

  setattr( rule_function, "__name__", name )

  existing_rule = getattr( rule_function, RULE_MARKER, None )
  existing_initialize_rule = getattr( rule_function, INITIALIZE_RULE_MARKER,
                                      None )
  if existing_rule is not None or existing_initialize_rule is not None:
    raise InvalidDefinition(
        'A function cannot be used for two distinct rules. ',
        Settings.default,
    )
  #precondition = getattr(rule_function, PRECONDITION_MARKER, None)
  arguments = cls.argument_strategy( method_name_fl )
  precondition = cls.precondition( method_name_fl )
  rule = Rule(
      targets=[],
      arguments=arguments,
      function=rule_function,
      precondition=precondition )

  setattr( rule_function, RULE_MARKER, rule )
  setattr( cls, name, rule_function )


#-------------------------------------------------------------------------
# ArgumentStrategy
#-------------------------------------------------------------------------
class ArgumentStrategy( object ):

  def __init__( s, **kwargs ):
    s.arguments = kwargs


#-------------------------------------------------------------------------
# argument_strategy
#-------------------------------------------------------------------------
ARGUMENT_STRATEGY_MARKER = u'pymtl-method-based-argument-strategy'


def argument_strategy(**kwargs ):
  """Decorator to apply an invariant for rules in a RuleBasedStateMachine.
    The decorated function will be run after every rule and can raise an
    exception to indicate failed invariants.

    For example::

        class MyTestMachine(RuleBasedStateMachine):
            state = 1

            @invariant()
            def is_nonzero(self):
                assert self.state != 0
    """

  def accept( f ):
    existing_argument_strategy = getattr( f, ARGUMENT_STRATEGY_MARKER, None )
    if existing_argument_strategy is not None:
      raise InvalidDefinition(
          'A function cannot be used for two distinct argument strategies.',
          Settings.default,
      )
    arguments = ArgumentStrategy(**kwargs )

    @proxies( f )
    def arguments_wrapper(*args, **kwargs ):
      return f(*args, **kwargs )

    setattr( arguments_wrapper, ARGUMENT_STRATEGY_MARKER, arguments )
    return arguments_wrapper

  return accept


#-------------------------------------------------------------------------
# Precondition
#-------------------------------------------------------------------------
@attr.s()
class ReferencePrecondition( object ):
  precondition = attr.ib()


#-------------------------------------------------------------------------
# precondition
#-------------------------------------------------------------------------
REFERENCE_PRECONDITION_MARKER = u'pymtl-method-based-precondition'


def reference_precondition( precond ):
  """Decorator to apply add precondition to an FL model, usually 
    enforces validity of datas

    For example::

        class TestFL:

            @precondition_fl( lambda machine, data: not data[ 'id' ] in machine.reference.snap_shot_free_list )
            def test_method_call( self, id ):
                ...
    """

  def accept( f ):
    existing_precondition = getattr( f, REFERENCE_PRECONDITION_MARKER, None )
    if existing_precondition is not None:
      raise InvalidDefinition(
          'A function cannot be used for two distinct preconditions.',
          Settings.default,
      )
    precondition = ReferencePrecondition( precondition=precond )

    @proxies( f )
    def precondition_wrapper(*args, **kwargs ):
      return f(*args, **kwargs )

    setattr( precondition_wrapper, REFERENCE_PRECONDITION_MARKER, precondition )
    return precondition_wrapper

  return accept


#-------------------------------------------------------------------------
# MethodOrder
#-------------------------------------------------------------------------
@attr.s()
class MethodOrder( object ):
  order = attr.ib()


class MethodStrategy:
  pass


#-------------------------------------------------------------------------
# CompareTest
#-------------------------------------------------------------------------
class CompareTest( TestStateMachine ):
  sim = None
  reference = None

  def __init__( self ):
    TestStateMachine.__init__( self )
    self.sim.reset()
    self.reference.reset()


#-------------------------------------------------------------------------
# create_test_state_machine
#-------------------------------------------------------------------------
def create_test_state_machine( model, reference, customized_methods=None ):
  method_specs = inspect_methods( model )
  WrapperClass, method_specs = create_wrapper_class(
      model, method_specs=method_specs, customized_methods=customized_methods )
  method_set_rtl = Set([ spec.method_name for spec in method_specs ] )
  sim = WrapperClass( model )

  Test = type(
      type( model ).__name__ + "TestStateMachine", CompareTest.__bases__,
      dict( CompareTest.__dict__ ) )

  method_set_fl = Set()
  for k, v in inspect.getmembers( reference ):
    method_name_fl = k.replace( "_call", "" )
    method_set_fl.add( method_name_fl )
    arguments = getattr( v, ARGUMENT_STRATEGY_MARKER, None )
    if arguments:
      Test.add_argument_strategy( method_name_fl, arguments.arguments )
    precondition = getattr( v, REFERENCE_PRECONDITION_MARKER, None )

    if precondition != None:
      Test.add_precondition( method_name_fl, precondition.precondition )

    if isinstance( v, MethodOrder ):
      Test.set_order( v.order )

    if isinstance( v, MethodStrategy ):
      for method, strategy in inspect.getmembers( v ):
        if isinstance( strategy, ArgumentStrategy ):
          Test.add_argument_strategy( method, strategy.arguments )

  # make sure that all RTL methods have counterpart in FL
  difference = method_set_rtl - method_set_fl
  if difference:
    error_msg = """
  Found RTL model method not in FL!
    - method name(s)    : {method_name}
"""
    raise RunMethodTestError(
        error_msg.format( method_name=", ".join( difference ) ) )

  # make sure that all method arguments have strategy specified
  error_msg = """
  Found argument with no strategy specified!
    - method name : {method_name}
    - arg         : {arg} 
"""
  for spec in method_specs:
    method_name = spec.method_name
    strategies = Test.argument_strategy( method_name )
    for arg in spec.arg.keys():
      if not strategies.has_key( arg ):
        raise RunMethodTestError(
            error_msg.format( method_name=method_name, arg=arg ) )

  # add rule
  for method_spec in method_specs:
    add_rule( Test, method_spec )

  Test.sim = sim
  Test.reference = reference

  return Test


#-------------------------------------------------------------------------
# generate_methods_from_model
#-------------------------------------------------------------------------
def generate_methods_from_model( model ):
  method_specs = inspect_methods( model )

  # get unique methods
  method_spec_dict = {}
  for spec in method_specs:
    method_spec_dict[ spec.method_name ] = spec

  for method_name, spec in method_spec_dict.items():
    arguments = ', '.join([ 's' ] + spec.arg.keys() )
    print "  def {}_call( {} ):".format( method_name, arguments )
    if spec.hasrdy:
      print "    assert s.{}_rdy()".format( method_name )
    return_list = [ "{}=0".format( ret ) for ret in spec.ret.keys() ]
    if return_list:
      print "    return ReturnValues( {} )".format( ", ".join( return_list ) )
    else:
      print "    pass"
    print ""

    if spec.hasrdy:
      print "  def {}_rdy( s ):".format( method_name )
      print "    return True"
      print ""

  print "  def reset( s ):"
  print "    pass"


#-------------------------------------------------------------------------
# bits_strategy
#-------------------------------------------------------------------------
def bits_strategy( nbits ):
  return st.integers( min_value=0, max_value=Bits( nbits )._max )


#-------------------------------------------------------------------------
# ReturnValues
#-------------------------------------------------------------------------


class ReturnValues:

  def __init__( s, **kwargs ):
    for k, v in kwargs.items():
      setattr( s, k, v )
