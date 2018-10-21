#=========================================================================
# adapters
#=========================================================================

from copy import deepcopy
from collections import deque

from pymtl import *

from pclib.cl import InValRdyQueueAdapter, OutValRdyQueueAdapter

#UnbufferedInValRdyQueueAdapter = InValRdyQueueAdapter
#UnbufferedOutValRdyQueueAdapter = OutValRdyQueueAdapter


#-------------------------------------------------------------------------
# UnbufferedInValRdyQueueAdapter
#-------------------------------------------------------------------------
class UnbufferedInValRdyQueueAdapter( object ):

  def __init__( s, in_ ):
    s.in_ = in_

  def empty( s ):
    return not s.in_.val or not s.in_.rdy

  def assert_rdy( s ):
    s.in_.rdy.next = 1

  def deq( s ):
    assert s.in_.val and s.in_.rdy
    item = deepcopy( s.in_.msg )
    return item

  def xtick( s ):
    s.in_.rdy.next = 0


#-------------------------------------------------------------------------
# UnbufferedOutValRdyQueueAdapter
#-------------------------------------------------------------------------


class UnbufferedOutValRdyQueueAdapter( object ):

  def __init__( s, out ):
    s.out = out
    s.data = None

  def full( s ):
    return s.data is not None

  def val( s ):
    return s.out.val

  def msg( s ):
    return s.out.msg

  def enq( s, item ):
    assert not s.full()
    s.data = deepcopy( item )
    s.out.msg.next = deepcopy( item )
    s.out.val.next = 1

  def xtick( s ):
    if s.out.rdy and s.out.val:
      s.data = None
    s.out.val.next = s.data is not None
