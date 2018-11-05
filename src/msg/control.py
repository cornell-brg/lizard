from pymtl import *
from config.general import *


class GetEpochStartRequest( BitStructDefinition ):

  def __init__( s ):
    s.epoch = BitField( INST_TAG_LEN )


class GetEpochStartResponse( BitStructDefinition ):

  def __init__( s ):
    s.pc = BitField( XLEN )
    s.valid = BitField( 1 )
    s.current_epoch = BitField( INST_TAG_LEN )


class RegisterInstrRequest( BitStructDefinition ):

  def __init__( s ):
    s.succesor_pc = BitField( XLEN )
    s.epoch = BitField( INST_TAG_LEN )


class RegisterInstrResponse( BitStructDefinition ):

  def __init__( s ):
    s.tag = BitField( INST_TAG_LEN )
    s.valid = BitField( 1 )
    s.current_epoch = BitField( INST_TAG_LEN )


class MarkSpeculativeRequest( BitStructDefinition ):

  def __init__( s ):
    s.tag = BitField( INST_TAG_LEN )


class MarkSpeculativeResponse( BitStructDefinition ):

  def __init__( s ):
    s.success = BitField( 1 )


class IsHeadRequest( BitStructDefinition ):

  def __init__( s ):
    s.tag = BitField( INST_TAG_LEN )


class IsHeadResponse( BitStructDefinition ):

  def __init__( s ):
    s.is_head = BitField( 1 )


class RedirectRequest( BitStructDefinition ):

  def __init__( s ):
    s.source_tag = BitField( INST_TAG_LEN )
    s.target_pc = BitField( XLEN )
    s.at_commit = BitField( 1 )
    # if 1, then regardless of the sucessor PC,
    # the controlflow unit will force a rediredct.
    # This is useful if even though the right instruction
    # was fetched, it needs to be fetched and run again.
    # For example, a FENCE.I instruction must redirect
    # and fetch again regardless of what was originally
    # fetched next.
    s.force_redirect = BitField( 1 )


class TagValidRequest( BitStructDefinition ):

  def __init__( s ):
    s.tag = BitField( INST_TAG_LEN )


class TagValidResponse( BitStructDefinition ):

  def __init__( s ):
    s.valid = BitField( 1 )


class RetireRequest( BitStructDefinition ):

  def __init__( s ):
    s.tag = BitField( INST_TAG_LEN )
