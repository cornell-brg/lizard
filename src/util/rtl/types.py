from pytml import *

class Array(object):
  def __init__(s, dtype, length):
    s.Data = canonicalize_type(dtype)
    s.length = length

def canonicalize_type( pymtl_type ):
  if isinstance( pymtl_type, int ):
    return Bits( pymtl_type )
  elif isinstance( pymtl_type, Array ):
    return Array(canonicalize_type(pymtl_type.Data, pymtl_type.length))
  else:
    return pymtl_type

