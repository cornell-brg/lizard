from pymtl import *


def bitstruct_values(s):
  return {key: hex(getattr(s, key).uint()) for key in s.bitfields.keys()}
