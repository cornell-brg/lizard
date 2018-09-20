#=========================================================================
# Integer Multiplier Fixed Latency RTL Model
#=========================================================================

from pymtl        import *
from pclib.ifcs   import InValRdyBundle, OutValRdyBundle

# ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Define datapath and control unit here.
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#=========================================================================
# Integer Multiplier Fixed Latency
#=========================================================================

class IntMulBasePRTL( Model ):

  # Constructor

  def __init__( s ):

    # Interface

    s.req    = InValRdyBundle  ( Bits(64) )
    s.resp   = OutValRdyBundle ( Bits(32) )

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Instantiate datapath and control models here and then connect them
    # together.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    IDLE = Bits (2, 0)
    CALC = Bits (2, 1)
    DONE = Bits (2, 2)
    s.state = Wire ( Bits(2) )
    
    s.counter = Wire ( Bits (6) )
    s.add = Wire ( Bits(1) )
    s.a = Wire ( Bits(32) )
    s.b = Wire ( Bits(32) )
    s.result = Wire ( Bits(32) )
    s.a_reg = Wire ( Bits(32) )
    s.b_reg = Wire ( Bits(32) )
    s.result_reg = Wire ( Bits(32) )
    
    s.a_mux_sel = Wire ( Bits (1) )
    s.b_mux_sel = Wire ( Bits (1) )
    s.result_mux_sel = Wire ( Bits (1) )
    s.result_en = Wire ( Bits (1) )
    s.add_mux_sel = Wire ( Bits (1) )
    s.b_lsb = Wire ( Bits (1) )

    @s.tick_rtl
    def block1():
      if s.reset:
        s.state.next = IDLE
      elif s.state == IDLE:
        if s.req.val == 1:
          s.state.next = CALC
        s.counter.next = 0
      elif s.state == CALC:
        if s.counter == 32:
          s.state.next = DONE
        else:
          s.counter.next = s.counter + 1
      elif s.state == DONE:
        if s.resp.rdy == 1:
          s.state.next = IDLE
      s.a.next = s.a_reg
      s.b.next = s.b_reg
      s.result.next = s.result_reg

    @s.combinational
    def block2():
      if s.state == IDLE:
        s.req.rdy.value = 1
        s.resp.val.value = 0
        s.a_mux_sel.value = 1
        s.b_mux_sel.value = 1
        s.result_mux_sel.value = 1
        s.result_en.value = 1
        s.add_mux_sel.value = 1
      elif s.state == CALC:
        s.req.rdy.value = 0
        s.resp.val.value = 0
        s.a_mux_sel.value = 0
        s.b_mux_sel.value = 0
        s.result_mux_sel.value = 0
        s.result_en.value = 1
        s.add_mux_sel.value = ~s.b_lsb
      else:
        s.req.rdy.value = 0
        s.resp.val.value = 1
        s.a_mux_sel.value = 1
        s.b_mux_sel.value = 1
        s.result_mux_sel.value = 1
        s.result_en.value = 0
        s.add_mux_sel.value = 1

    @s.combinational
    def block3():
      if s.b_mux_sel == 1:
        s.b_reg.value = s.req.msg[32:64]
      else:
        s.b_reg.value = s.b >> 1
        s.b_lsb.value = s.b[0]
      if s.a_mux_sel == 1:
        s.a_reg.value = s.req.msg[0:32]
      else:
        s.a_reg.value = s.a << 1
      if s.result_en == 1:
        if s.result_mux_sel == 1:
          s.result_reg.value = 0
        elif s.add_mux_sel == 1:
          s.result_reg.value = s.result
        else:
          s.result_reg.value = s.result + s.a
      s.resp.msg.value = s.result
            

  # Line tracing

  def line_trace( s ):

    # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add additional line tracing using the given line_trace_str for
    # internal state including the current FSM state.
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    line_trace_str = "a:{} b:{} r:{} s:{} c:{}".format(s.a, s.b, s.result, s.state, s.counter)

    return "{}({}){}".format(
      s.req,
      line_trace_str,
      s.resp,
    )

