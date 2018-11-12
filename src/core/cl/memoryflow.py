from pymtl import *
from msg.mem import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort
from config.general import *
from copy import deepcopy


class MemoryFlowManagerCL( Model ):
  """
  A simple memory flow manager which only accepts one request 
  in flight at once. No more requests can be accepted until
  the current request is retired.
  """

  def __init__( s ):
    s.current = None
    s.submitted = False
    s.resp_received = True
    s.resp = None
    s.drop_count = 0

    s.mem_req = OutValRdyCLPort( MemMsg8B.req )
    s.mem_resp = InValRdyCLPort( MemMsg8B.resp )

  def xtick( s ):
    if s.reset:
      s.current = None
      s.submitted = False
      s.resp_received = True
      s.resp = None
      s.drop_count = 0
      return

    if not s.mem_resp.empty():
      if s.drop_count > 0:
        s.mem_resp.deq()
        s.drop_count -= 1
      else:
        s.resp_received = True
        s.resp = s.mem_resp.deq()

  def busy( s ):
    return s.current is not None or s.mem_req.full()

  def stage( s, request ):
    s.current = deepcopy( request )
    s.submitted = False
    s.resp_received = False
    s.resp = None

  def submit( s ):
    s.mem_req.enq( s.current )
    s.submitted = True

  def response_ready( s ):
    return s.resp_received

  def await_response( s ):
    if not s.resp_received:
      return None
    else:
      return s.resp

  def retire( s ):
    s.current = None
    # If no response has been received yet, drop it
    if not s.resp_received and s.submitted:
      s.drop_count += 1
    s.submitted = False
    # s.resp_received = True

  def commit( s ):
    if not s.submitted:
      s.submit()
    s.retire()
