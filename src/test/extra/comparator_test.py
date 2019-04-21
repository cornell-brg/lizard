from pymtl import *
from util.rtl.comparator import ComparatorInterface, Comparator
from model.translate import translate


def test_translation():
  translate(Comparator(ComparatorInterface(64)))
