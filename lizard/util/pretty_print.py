from pymtl import *


def bitstruct_values(s):
  return {key: hex(getattr(s, key).uint()) for key in s.bitfields.keys()}


def list_string(lst):
  return ", ".join([str(x) for x in lst])


def list_string_value(lst):
  str_list = []
  for x in lst:
    if isinstance(x, BitStruct):
      str_list += [bitstruct_values(x)]
    else:
      str_list += [str(x)]
  return ", ".join(str_list)
