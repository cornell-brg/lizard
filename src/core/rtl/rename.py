from pymtl import *
from bitutil import clog2

#-----------------------------------------------------------------------
# RegisterFileRst
#-----------------------------------------------------------------------
class RegisterFileRst( Model ):

  def __init__( s, dtype = Bits(32), nregs = 32, rd_ports = 1, wr_ports = 1,
                   const_zero=False, reset_values=[0]*32 ):
    addr_nbits  = clog2( nregs )

    s.rd_addr  = [ InPort ( addr_nbits ) for _ in range(rd_ports) ]
    s.rd_data  = [ OutPort( dtype )      for _ in range(rd_ports) ]

    if wr_ports == 1:
      s.wr_addr  = InPort( addr_nbits )
      s.wr_data  = InPort( dtype )
      s.wr_en    = InPort( 1 )
    else:
      s.wr_addr  = [ InPort( addr_nbits ) for _ in range(wr_ports) ]
      s.wr_data  = [ InPort( dtype )      for _ in range(wr_ports) ]
      s.wr_en    = [ InPort( 1 )          for _ in range(wr_ports) ]

    s.regs = [ Wire( dtype ) for _ in range( nregs ) ]

    #-------------------------------------------------------------------
    # Combinational read logic
    #-------------------------------------------------------------------

    # constant zero

    if const_zero:

      @s.combinational
      def comb_logic():
        for i in range( rd_ports ):
          assert s.rd_addr[i] < nregs
          if s.rd_addr[i] == 0:
            s.rd_data[i].value = 0
          else:
            s.rd_data[i].value = s.regs[ s.rd_addr[i] ]

    else:

      @s.combinational
      def comb_logic():
        for i in range( rd_ports ):
          assert s.rd_addr[i] < nregs
          s.rd_data[i].value = s.regs[ s.rd_addr[i] ]

    # Select write logic depending on if this register file should have
    # a constant zero register or not!

    #-------------------------------------------------------------------
    # Sequential write logic, single write port
    #-------------------------------------------------------------------
    if wr_ports == 1 and not const_zero:

      @s.posedge_clk
      def seq_logic():
        if s.reset:
          for i in range( nregs ):
            s.regs[i].next = reset_values[i]
        elif s.wr_en:
          s.regs[ s.wr_addr ].next = s.wr_data

    #-------------------------------------------------------------------
    # Sequential write logic, single write port, constant zero
    #-------------------------------------------------------------------
    elif wr_ports == 1:

      @s.posedge_clk
      def seq_logic_const_zero():
        if s.reset:
          for i in range( nregs ):
            s.regs[i].next = reset_values[i]
        elif s.wr_en and s.wr_addr != 0:
          s.regs[ s.wr_addr ].next = s.wr_data

    #-------------------------------------------------------------------
    # Sequential write logic, multiple write ports
    #-------------------------------------------------------------------
    elif not const_zero:

      @s.posedge_clk
      def seq_logic_multiple_wr():
        if s.reset:
          for i in range( nregs ):
            s.regs[i].next = reset_values[i]
        else:
          for i in range( wr_ports ):
            if s.wr_en[i]:
              s.regs[ s.wr_addr[i] ].next = s.wr_data[i]

    #-------------------------------------------------------------------
    # Sequential write logic, multiple write ports, constant zero
    #-------------------------------------------------------------------
    else:

      @s.posedge_clk
      def seq_logic_multiple_wr():
        if s.reset:
          for i in range( nregs ):
            s.regs[i].next = reset_values[i]
        else:
          for i in range( wr_ports ):
            if s.wr_en[i] and s.wr_addr[i] != 0:
              s.regs[ s.wr_addr[i] ].next = s.wr_data[i]

  def line_trace( s ):
    return [ x.uint() for x in s.regs ]

#-------------------------------------------------------------------------
# GetRenameRdyCallOutBundle
#-------------------------------------------------------------------------
class GetRenameRdyCallOutBundle( PortBundle ):

  #-----------------------------------------------------------------------
  # __init__
  #-----------------------------------------------------------------------
  # Interface for the ValRdy PortBundle.
  def __init__( self, naregs, npregs ):
    self.x = InPort ( clog2( naregs ) )
    self.p = OutPort ( clog2( npregs ) )
    self.call = InPort ( 1 )
    self.rdy = OutPort( 1 )

#-------------------------------------------------------------------------
# RenameRdyCallOutBundle
#-------------------------------------------------------------------------
class RenameRdyCallOutBundle( PortBundle ):

  #-----------------------------------------------------------------------
  # __init__
  #-----------------------------------------------------------------------
  # Interface for the ValRdy PortBundle.
  def __init__( self, naregs, npregs ):
    self.x = InPort ( clog2( naregs ) )
    self.p = InPort ( clog2( npregs ) )
    self.call = InPort ( 1 )
    self.rdy = OutPort( 1 )
    
OutGetRenameRdyCallOutBundle, InGetRenameRdyCallOutBundle = create_PortBundles( GetRenameRdyCallOutBundle )
OutRenameRdyCallOutBundle, InRenameRdyCallOutBundle = create_PortBundles( RenameRdyCallOutBundle )

#-------------------------------------------------------------------------
# RenameTableRTL
#-------------------------------------------------------------------------
class RenameTableRTL ( Model ):
  
  def __init__( s, naregs, npregs ):
    s.nbits = clog2( npregs )
    
    # GetRename, Rename ports
    s.get_rename = OutGetRenameRdyCallOutBundle( naregs, npregs )
    s.rename = OutRenameRdyCallOutBundle( naregs, npregs )
    
    # RegisterFile
    s.rf = m = RegisterFileRst( dtype=Bits( clog2( npregs ) ), nregs=naregs, const_zero=True, reset_values=[ x for x in range( naregs ) ] )
    s.connect_pairs(
      m.rd_addr[0],    s.get_rename.x,
      m.rd_data[0],    s.get_rename.p,
      m.wr_en,         s.rename.call,
      m.wr_addr,       s.rename.x,
      m.wr_data,       s.rename.p
    )
  
    @s.posedge_clk
    def seq_logic_set_rdy_signals():
      s.get_rename.rdy.next = 1
      s.rename.rdy.next = 1
      
    # Uncommenting this block and commenting out "m.rd_data[0],    s.get_rename.p," in s.connect_pairs
    # will bypass rename.p to get_rename.p. This does not match with FL model and will cause test to fail
    '''@s.combinational
    def comb():
      if s.get_rename.x == s.rename.x and s.rename.call:
        s.get_rename.p.value = s.rename.p
      else:
        s.get_rename.p.value = s.rf.rd_data[0]
    '''
      
  def line_trace( s ):
    rename_trace = "rename x{: <{width}} to p{: <{width}}".format( s.rename.x , s.rename.p, width=s.nbits ) if s.rename.call else ""
    get_rename_trace = "get_rename x{: <{width}}: p{: <{width}}".format( s.get_rename.x , s.get_rename.p, width=s.nbits  ) if s.get_rename.call else ""
    return "{: <{width}} () {: <{width}}".format( rename_trace , get_rename_trace, width=24 )
  
