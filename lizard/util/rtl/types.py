from pymtl import *


def type_str(pymtl_type):
  dim_spec = ''
  current = pymtl_type
  while isinstance(current, Array):
    dim_spec = '{}[{}]'.format(dim_spec, current.length)
    current = current.Data

  if len(dim_spec) != 0:
    dim_spec = ' {}'.format(dim_spec)

  if isinstance(current, Bits):
    return 'Bits({}){}'.format(current.nbits, dim_spec)
  else:
    raise ValueError('Unknown type: {}'.format(pymtl_type))


class Array(object):
  """Represents an array type for hardware modeling
  """

  def __init__(s, dtype, length):
    s.Data = canonicalize_type(dtype)
    s.length = length


def canonicalize_type(pymtl_type):
  """Computes an equivelent canonical type for a given type.

  Integers are promoted to Bits, and arrays are recursively canonicalized.
  """
  if isinstance(pymtl_type, int):
    return Bits(pymtl_type)
  elif isinstance(pymtl_type, Array):
    return Array(canonicalize_type(pymtl_type.Data), pymtl_type.length)
  else:
    return pymtl_type
