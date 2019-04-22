from pymtl import *
from tests.context import lizard
from lizard.util.rtl.comparator import ComparatorInterface, Comparator
from lizard.model.translate import translate


def test_translation():
  translate(Comparator(ComparatorInterface(64)))
