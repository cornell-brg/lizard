#=========================================================================
# test for Rename Table
#=========================================================================
from pymtl import *
from method_based import TestStateMachine
from hypothesis.stateful import run_state_machine_as_test, Bundle, rule, precondition
import hypothesis.strategies as st

from core.rtl.rename import RenameTableRTL

class RenameTableFL ( Model ):

  def __init__( self, naregs, npregs ):
    self.naregs = naregs
    self.npregs = npregs
    self.npbits = clog2( npregs )
    self.rename_table = [ Bits( self.npbits ) for _ in range( naregs ) ]
    
  def fl_reset( self ):
    for x in range( len( self.rename_table ) ):
      self.rename_table[ x ] = Bits( self.npbits, x )
  
  def rename_rdy( self ):
    return 1
      
  def rename_call( self, x, p ):
    assert self.rename_rdy()
    assert x < self.naregs and x >= 0
    assert p < self.npregs and p >= 0
    
    # x0 does not get rewrite
    if x == 0:
      return
      
    self.rename_table[ x ] = p
  
  def get_rename_rdy( self ):
    return 1
    
  def get_rename_call( self, x ):
    assert self.get_rename_rdy()
    assert x < self.naregs and x >= 0
    return { "p": self.rename_table[ x ] }
  
  def line_trace( self ):
    return ""
  
  def __str__( self ):
    return str( self.rename_table )


class RenameTableRTLWrapper:
  def __init__ ( s, model ) :
    s.model = model
    s.model.elaborate()  
    s.sim = SimulationTool( s.model )
  
  def rtl_reset( s ):
    s.sim.reset()
    s.sim.cycle()
    
  def cycle( s ):    
    s.sim.print_line_trace()
    s.sim.cycle()
    s.clear()
    s.sim.eval_combinational()
  
  def get_rename_rdy( s ):
    return s.model.get_rename.rdy
    

  def get_rename_call( s, x ):
    assert s.get_rename_rdy()
    s.model.get_rename.call.value = 1
    s.model.get_rename.x.value = x
    s.sim.eval_combinational()
    return { 'p': s.model.get_rename.p }
  
  def rename_rdy( s ):
    return s.model.rename.rdy
    
  def rename_call ( s, x, p ) :
    assert s.rename_rdy()
    s.model.rename.x.value = x
    s.model.rename.p.value = p
    s.model.rename.call.value = 1
    s.sim.eval_combinational()
    
  def clear( s ):
    s.model.rename.call.value = 0
    s.model.get_rename.call.value = 0
   

naregs = 10
npregs = 20
class RenameTest(TestStateMachine):
  def __init__( self ):
    super(RenameTest, self).__init__()
    self.sim = RenameTableRTLWrapper( RenameTableRTL( naregs, npregs ) )
    self.reference = RenameTableFL( naregs, npregs )
    self.reference.fl_reset()
    self.sim.rtl_reset()
  
  __name__ = "RenameTest"
  
  x_bundle = Bundle('x')
  p_bundle = Bundle('p')

  @rule( target=x_bundle, x=st.integers( min_value = 0, max_value = naregs - 1 ) )
  def x( self, x ):
    return x
    
  @rule( target=p_bundle, p=st.integers( min_value = 0, max_value = npregs - 1 ) )
  def p( self, p ):
    return p
    
  @rule( x=x_bundle, p=p_bundle )
  def rename( self, x, p ):
    pass
    
  # In the rename table, when get_rename and rename are called on the same 
  # areg in the same cycle, ger_rename should always return the
  # old value.
  #
  # The order that rename and get_rename get called does not matter in RTL
  # since the logic is combinational, but does matter for FL and can produce 
  # wrong result.
  #
  # This precondition is a hack to enforce that get_rename is never called 
  # after rename in one cycle. The same cycle cases are tested when 
  # get_rename is called before rename
  @precondition( lambda self: not self.sim.model.rename.call  )
  @rule( x=x_bundle )
  def get_rename( self, x ):
    pass

def test_state_machine():
  run_state_machine_as_test( RenameTest )
  
def test_direct():
  sim = RenameTableRTLWrapper( RenameTableRTL( 10, 20 ) )
  sim.rtl_reset()
  
  # writing x0 gets ignored
  assert sim.rename_rdy()
  sim.rename_call( 0, 1 )
  sim.cycle()
  assert sim.get_rename_rdy()
  assert sim.get_rename_call( 0 )['p'] == 0
  sim.cycle()
  
  # rename/get_rename in same cycle
  assert sim.get_rename_rdy()
  get_result = sim.get_rename_call( 1 )
  assert sim.rename_rdy()
  sim.rename_call( 1, 2 )
  assert get_result['p'] == 1
  sim.cycle()
  assert sim.get_rename_rdy()
  assert sim.get_rename_call( 1 )['p'] == 2
