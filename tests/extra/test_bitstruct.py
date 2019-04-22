from pymtl import *
from tests.context import lizard
from lizard.util.test_utils import create_test_bitstruct


class BitstructType(BitStructDefinition):

  def __init__(s):
    s.a = BitField(1)
    s.b = BitField(2)
    s.c = BitField(3)


def test_set_dc():
  bitstruct = BitstructType()
  bitstruct.a = 0
  bitstruct.b = 2
  bitstruct.c = 3

  TestBitStruct = create_test_bitstruct(bitstruct)
  TestBitStruct.set_dc(lambda x: x.a, ['b', 'c'])

  test_bitstruct = TestBitStruct()

  assert (test_bitstruct != bitstruct)
  assert (not test_bitstruct == bitstruct)

  # comparing to value
  assert (test_bitstruct != int(bitstruct))
  assert (not test_bitstruct == int(bitstruct))

  # don't care
  bitstruct.a = 1
  test_bitstruct.a = 1
  assert (test_bitstruct == bitstruct)
  assert (not test_bitstruct != bitstruct)

  # comparing to value
  assert (test_bitstruct == int(bitstruct))
  assert (not test_bitstruct != int(bitstruct))


def test_set_eq():
  bitstruct = BitstructType()
  bitstruct.a = 0
  bitstruct.b = 2
  bitstruct.c = 3

  def equal(s, other):
    if s.a:
      s.b = 0
      s.c = 0
      other.b = 0
      other.c = 0
    return other == s

  TestBitStruct = create_test_bitstruct(bitstruct, equal)

  test_bitstruct = TestBitStruct()

  bitstruct_value = int(bitstruct)
  test_bitstruct_value = int(test_bitstruct)

  assert (test_bitstruct != bitstruct)
  assert (not test_bitstruct == bitstruct)

  # comparing to value
  assert (test_bitstruct != int(bitstruct))
  assert (not test_bitstruct == int(bitstruct))

  # makesure that __eq__ does not modify either side
  assert (int(bitstruct) == bitstruct_value)
  assert (int(test_bitstruct) == test_bitstruct_value)

  # don't care
  bitstruct.a = 1
  test_bitstruct.a = 1

  bitstruct_value = int(bitstruct)
  test_bitstruct_value = int(test_bitstruct)

  assert (test_bitstruct == bitstruct)
  assert (not test_bitstruct != bitstruct)

  # comparing to value
  assert (test_bitstruct == int(bitstruct))
  assert (not test_bitstruct != int(bitstruct))

  # makesure that __eq__ does not modify either side
  assert (int(bitstruct) == bitstruct_value)
  assert (int(test_bitstruct) == test_bitstruct_value)
