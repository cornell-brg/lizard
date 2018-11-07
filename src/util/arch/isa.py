import struct

import abc
from pymtl import Bits, concat
from string import translate, maketrans
from util.sparse_memory_image import SparseMemoryImage
from config.general import *
from msg.codes import *
from collections import namedtuple
from bitutil import bslice, byte_count


class FieldFormat( object ):
  """
  Represents: a format for a field in an assembly instruction.
  """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def parse( self, sym, pc, spec ):
    """
    Given a field as the string spec, the current PC,
    and a symbol table (a mapping from symbol names to addresses),
    parse the given string, and return the parsed value.
    """
    pass

  @abc.abstractmethod
  def format( self, value ):
    """
    Given the value, format the value in such a way such that
    format(parse({}, 0, format(value))) == format(value)
    """
    pass


class IntFormat( FieldFormat ):
  """
  Represents:
  A simple assembly field formatter.
  Fields are plain integers, and are formatter as integers
  """

  def parse( self, sym, pc, spec ):
    return int( spec, 0 )

  def format( self, value ):
    return str( value )


class FieldSpec( object ):
  """
  Represents: a field specifier. A field is a value encoded into
  some positions inside an instruction.
  A field is specified by its width, the total number of bits involved,
  and by a mapping from slices in the value to slices in the target instruction.
  This is represented as an association list by parts. 
  For example, consider the following 32 instruction with a strange 29 bit imm:

   31                16 15 13 12        0
  | imm[28:13]         |     | imm[12:0] |

  This could be encoded as:

  FieldSpec(29, IntFormat(), [(bslice(31, 16), bslice(28, 13)), (bslice(12, 0), bslice(12, 0))])

  A simple case occurs when the value is not split across multiple areas.
  In this case, it can be represented by only its location in the encoded
  instruction:

  FieldSpec(3, IntFormat(), bslice(7, 4))

  One special case is where some bits in the value are not actually encoded, but 
  are instread required to be fixed values. In that case, instead of including
  a slice indicating a position in the target, include a value instead:

  FieldSpec(3, IntFormat(), [(bslice(2,1), bslice(2, 1), (0, bslice(0))]

  The above spec means that only the 2 high bits of the field are actually encoded
  in the target, while the low bit must be 0.
  """

  def __init__( self, width, formatter, parts ):
    self.width = width
    self.formatter = formatter
    if isinstance( parts, slice ):
      self.parts = [( parts, bslice( self.width - 1, 0 ) ) ]
    else:
      self.parts = parts

  def assemble( self, target, value ):
    """
    Effect: copies the value into the appropriate positions in the target
    """
    value = Bits( self.width, value )
    for target_slice, field_slice in self.parts:
      if isinstance( target_slice, slice ):
        target[ target_slice ] = value[ field_slice ]
      elif value[ field_slice ] != target_slice:
        raise ValueError(
            "Incorrect value in slice {} of field {}: found: {} expected: {}"
            .format( field_slice, value, value[ field_slice ], target_slice ) )

  def disassemble( self, source ):
    """
    Computes the value by extracting and concatenating the individual parts from the source
    Returns: a Bits object of size width with the extracted value
    """
    result = Bits( self.width, 0 )
    for target_slice, field_slice in self.parts:
      if isinstance( target_slice, slice ):
        result[ field_slice ] = source[ target_slice ]
      else:
        result[ field_slice ] = target_slice
    return result

  def parse( self, sym, pc, spec ):
    """
    Parses the given spec using the symbol table and PC with this field's
    format
    """
    result = self.formatter.parse( sym, pc, spec )
    assert int( result ) < 2**self.width
    return result

  def format( self, value ):
    """
    Formats the value witht this field's format.
    """
    return self.formatter.format( value )

  def translate( self, target, sym, pc, spec ):
    """
    Effect: parses the spec using parse, and then assembles the value
    into target.
    """
    self.assemble( target, self.parse( sym, pc, spec ) )

  def decode( self, source ):
    """
    Effect: extracts the value using disassemble, and then format it
    using format.
    """
    return self.format( self.disassemble( source ) )


def split_instr( instr ):
  """
  Given an instruction of the form "name arg1, arg2, ...",
  returns the pair ("name", "arg1, arg2, ...").

  If the instruction has no arguments, the second element of
  the pair is the empty string.
  """
  result = instr.split( None, 1 )
  if len( result ) == 1:
    return result[ 0 ], ""
  else:
    return result


def simplify_args( args ):
  """
  Given a string argument list of the form "arg1, arg2, ...",
  or any variant such as "arg1(arg2)", returns the list
  ["arg1", "arg2", ...]
  """
  return translate( args, maketrans( ",()", "   " ) ).split()


def expand_gen( func ):
  """
  Function decorator, which given a function func, generates a new function, g,
  that given a list of tuples, maps func over the list, and flattens the result.

  Note that the tuples are splatted into func.
  """

  def loop( rows ):
    result = []
    for row in rows:
      temp = func(*row )
      if not isinstance( temp, list ):
        temp = [ temp ]
      result += temp
    return result

  return loop


@expand_gen
def expand_encoding( inst, opcode_mask, opcode ):
  """
  Given an instruction description of the form inst, opcode_mask, and opcode,
  computes a more usable 5 term expansion:

  name, args, simplify_args( args ), opcode_mask, opcode
  """
  name, args = split_instr( inst )
  return name, args, simplify_args( args ), opcode_mask, opcode


@expand_gen
def expand_pseudo_spec( pseudo, bases ):
  """
  Given a pseudo instruction specificion of the form pseudo, base_list,
  computes a more usable 3 term expansion:

  pseudo_name, simplify_args( pseudo_args ), bases_expanded

  where bases_expanded produced by mapoping split_instr over the base_list.
  """
  pseudo_name, pseudo_args = split_instr( pseudo )
  bases_expanded = [ split_instr( base ) for base in bases ]
  return pseudo_name, simplify_args( pseudo_args ), bases_expanded


InstSpec = namedtuple( 'InstSpec', 'args simple_args opcode_mask opcode' )
PseudoSpec = namedtuple( 'PseudoSpec', 'simple_args base_list' )


class Isa( object ):

  def __init__( self, ilen, xlen, inst_encoding_table, pseudo_table, fields ):

    self.ilen = ilen
    self.ilen_bytes = byte_count( ilen )
    self.xlen = xlen
    self.xlen_bytes = byte_count( xlen )
    self.encoding = {}
    self.pseudo_map = {}
    self.fields = fields

    for name, args, simple_args, opcode_mask, opcode in inst_encoding_table:
      self.encoding[ name ] = InstSpec( args, simple_args, opcode_mask, opcode )

    for name, simple_args, base_list in pseudo_table:
      self.pseudo_map[ name ] = PseudoSpec( simple_args, base_list )

  def expand_pseudo_instructions( self, inst_str ):
    name, args = split_instr( inst_str )
    if name in self.encoding:
      return [ inst_str ]
    elif name in self.pseudo_map:
      simple = simplify_args( args )
      var_names = self.pseudo_map[ name ].simple_args
      assert len( simple ) == len( var_names )
      arg_map = zip( var_names, simple )
      result = []
      for base_name, base_args in self.pseudo_map[ name ].base_list:
        for var, value in arg_map:
          base_args = base_args.replace( "${}".format( var ), value )
        result.append( "{} {}".format( base_name, base_args ) )
      return result
    else:
      raise ValueError( "Unknown instruction: {}".format( inst_str ) )

  def decode_inst_name( self, inst_bits ):
    for name, spec in self.encoding.iteritems():
      if ( inst_bits & spec.opcode_mask ) == spec.opcode:
        return name
    return 'invld'

  def assemble_inst( self, sym, pc, inst_str ):
    name, args = split_instr( inst_str )
    arg_list = simplify_args( args )

    result = Bits( self.ilen, self.encoding[ name ].opcode )

    for asm_field_str, field_name in zip( arg_list,
                                          self.encoding[ name ].simple_args ):
      self.fields[ field_name ].translate( result, sym, pc, asm_field_str )
    return result

  def disassemble_inst( self, inst_bits ):
    name = self.decode_inst_name( inst_bits )

    arg_str = self.encoding[ name ].args
    for field_name in self.encoding[ name ].simple_args:
      arg_str = arg_str.replace( field_name,
                                 self.fields[ field_name ].decode( inst_bits ) )

    return "{} {}".format( name, arg_str )
