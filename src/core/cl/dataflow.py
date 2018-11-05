from msg.data import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.cl import InValRdyQueueAdapter, OutValRdyQueueAdapter
from config.general import *
from msg.codes import *
from util.freelist.fl import FreeListFL


class PregState( BitStructDefinition ):

  def __init__( s ):
    s.value = BitField( XLEN )
    s.ready = BitField( 1 )
    s.areg = BitField( REG_SPEC_LEN )


class DataFlowManagerCL( Model ):

  def __init__( s ):
    # Reserve the highest tag for x0
    s.free_regs = FreeListFL( REG_TAG_COUNT - 1 )
    s.zero_tag = Bits( REG_TAG_LEN, REG_TAG_COUNT - 1 )
    s.rename_table = [ Bits( REG_TAG_LEN ) for _ in range( REG_COUNT ) ]
    s.preg_file = [ PregState() for _ in range( REG_TAG_COUNT ) ]
    s.areg_file = [ Bits( REG_TAG_LEN ) for _ in range( REG_COUNT ) ]

    s.mngr2proc = InValRdyBundle( Bits( XLEN ) )
    s.proc2mngr = OutValRdyBundle( Bits( XLEN ) )

    # size of None means it can grow arbitraily large
    s.mngr2proc_q = InValRdyQueueAdapter( s.mngr2proc, size=None )
    s.proc2mngr_q = OutValRdyQueueAdapter( s.proc2mngr, size=None )

  def xtick( s ):
    if s.reset:
      s.free_regs.fl_reset()
      for areg in range( REG_COUNT ):
        tag = s.get_dst( areg ).tag
        s.write_tag( tag, 0 )
        s.commit_tag( tag, True )
      s.csr_file = {}

    s.forwards = {}
    s.mngr2proc_q.xtick()
    s.proc2mngr_q.xtick()

  def get_rename_table( s ):
    return list( s.rename_table )

  def set_rename_table( s, rename_table ):
    s.rename_table = list( rename_table )

  def rollback_to_arch_state( s ):
    s.rename_table = list( s.areg_file )

  def get_src( s, areg ):
    resp = GetSrcResponse()
    if areg != 0:
      resp.tag = s.rename_table[ areg ]
      resp.ready = s.preg_file[ resp.tag ].ready
    else:
      resp.tag = s.zero_tag
      resp.ready = 1
    return resp

  def get_dst( s, areg ):
    resp = GetDstResponse()
    if areg != 0:
      preg = s.free_regs.alloc()
      if preg is None:
        resp.success = 0
      else:
        s.rename_table[ areg ] = preg
        resp.success = 1
        resp.tag = preg
        preg_entry = s.preg_file[ preg ]
        preg_entry.ready = 0
        preg_entry.areg = areg
    else:
      resp.success = 1
      resp.tag = s.zero_tag
    return resp


  def forward( s, data ):
    assert int(data.tag) not in s.forwards
    s.forwards[int(data.tag)] = data


  def read_tag( s, tag ):
    resp = ReadTagResponse()
    if tag != s.zero_tag:
      if int(tag) in s.forwards: # Can we forward it?
        resp.ready = 1
        resp.value = s.forwards[int(tag)].value
      else:
        preg = s.preg_file[ tag ]
        resp.ready = preg.ready
        resp.value = preg.value
    else:
      resp.ready = 1
      resp.value = 0
    return resp

  def write_tag( s, tag, value ):
    if tag != s.zero_tag:
      preg = s.preg_file[ tag ]
      preg.value = value
      preg.ready = 1

  def free_tag( s, tag ):
    if tag != s.zero_tag:
      s.free_regs.free( tag )

  def commit_tag( s, tag, initial=False ):
    if tag != s.zero_tag:
      preg = s.preg_file[ tag ]
      if not initial:
        # Free the old one
        s.free_regs.free( s.areg_file[ preg.areg ] )
      s.areg_file[ preg.areg ] = tag

  def read_csr( s, csr_num ):
    if csr_num == CsrRegisters.mngr2proc:
      if s.mngr2proc_q.empty():
        return None, False
      else:
        return s.mngr2proc_q.deq(), True
    else:
      return s.csr_file.get( int( csr_num ), Bits( XLEN, 0 ) ), True

  def write_csr( s, csr_num, value ):
    if csr_num == CsrRegisters.proc2mngr:
      # can grow forever, so enq will always work
      s.proc2mngr_q.enq( value )
    else:
      s.csr_file[ int( csr_num ) ] = value

  def line_trace( s ):
    return "<dataflowfl>"
