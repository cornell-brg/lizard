import hypothesis.strategies as st
from hypothesis.stateful import *
from hypothesis.vendor.pretty import CUnicodeIO, RepresentationPrinter

from pymtl import *

#-------------------------------------------------------------------------
# MethodBasedRuleStrategy
#-------------------------------------------------------------------------
class MethodBasedRuleStrategy( SearchStrategy ):
  def __init__( self, machine ):
    SearchStrategy.__init__( self )
    self.machine = machine
    self.rules = list( machine.rules() )
    # The order is a bit arbitrary. Primarily we're trying to group rules
    # that write to the same location together, and to put rules with no
    # target first as they have less effect on the structure. We order from
    # fewer to more arguments on grounds that it will plausibly need less
    # data. This probably won't work especially well and we could be
    # smarter about it, but it's better than just doing it in definition
    # order.
    self.rules.sort( 
      key=lambda rule: (
        sorted(rule.targets), len(rule.arguments),
        rule.function.__name__,
      ) 
    )

  def do_draw(self, data):
    # This strategy draw a randomly selected number of rules and do not care about
    # validity. In execute_step(step), only valid rules will be fired. We do this to
    # test possible dependencies - some rules are not valid in the first place become
    # valid if some other rules fire in the same cycle
    n = len(self.rules)
    rule_to_fire = []
    remaining_rules = [ i for i in range( 0, n ) ]
    num_rules = cu.integer_range( data, 1, n - 1 )
    for _ in range( num_rules ):
      i = cu.integer_range( data, 0, len( remaining_rules ) - 1 )
      rule_to_fire += [ self.rules[ remaining_rules[i] ] ]
      del remaining_rules[i]
    
    if rule_to_fire:
      return [ ( rule, data.draw( rule.arguments_strategy ) ) for rule in rule_to_fire ]

#-------------------------------------------------------------------------
# TestStateMachine
#-------------------------------------------------------------------------
class TestStateMachine( RuleBasedStateMachine ) :
  def __init__( self ):
    super( TestStateMachine, self ).__init__()
    self.__rules_strategy = MethodBasedRuleStrategy( self )
    self.__stream = CUnicodeIO()
    self.__printer = RepresentationPrinter( self.__stream )

  def compare_result( self, m_result, r_result ):
    if r_result:
      if not len( m_result ) == len( r_result ):
        self.sim.cycle()
        print "========================== error =========================="
        assert(False)
      for k in r_result.keys():
          if not m_result[k] == r_result[k]:
            self.sim.cycle()
            print "========================== error =========================="
            assert(False)
      

  def steps(self):
    # Pick initialize rules first
    if self._initialize_rules_to_run:
      return one_of(
        [
          tuples( just(rule), fixed_dictionaries( rule.arguments ) )
            for rule in self._initialize_rules_to_run
        ]
      )
    return self.__rules_strategy


  def execute_step(self, step):
    # store result of sim and reference
    s_results = []
    r_results = []
    
    # go though all rules for this step
    for ruledata in step:
      rule, data = ruledata
      data = dict( data )
      
      # For dependency reason we do allow rules invalid in the first place
      # to be added to step.
      # See MethodBasedRuleStrategy for more
      if not self.is_valid( rule ):
        continue
        
      for k, v in list( data.items() ):
        if isinstance( v, VarReference ):
          data[k] = self.names_to_values[ v.name ]
      result = rule.function( self, **data )
      
      # For method based interface rules, call rdy ones only
      name = rule.function.__name__
      sim_class_members = self.sim.__class__.__dict__
      reference_class_members = self.reference.__class__.__dict__
      
      if name + "_call" in sim_class_members.keys():
        if sim_class_members[ name + "_rdy" ]( self.sim ):
          s_results += [ sim_class_members[name + "_call" ]( self.sim, **data ) ]
          r_results += [ reference_class_members[name + "_call" ]( self.reference, **data ) ]
      
      # Generate values for bundle
      if rule.targets:
        name = self.new_name()
        self.names_to_values[ name ] = result
        self.__printer.singleton_pprinters.setdefault(
          id( result ), lambda obj, p, cycle: p.text( name )
        )
        for target in rule.targets:
          self.bundle( target ).append( VarReference( name ) )

      if self._initialize_rules_to_run:
          self._initialize_rules_to_run.remove( rule )  

    for s_result, r_result in zip( s_results, r_results ):
      self.compare_result( s_result, r_result )
      
    self.sim.cycle()
  
  def print_step( self, step ):
    pass

  def is_valid( self, rule ):
    if rule.precondition and not rule.precondition( self ):
      return False
    for b in rule.bundles:
      bundle = self.bundle( b.name )
      if not bundle:
        return False
    return True
