from pymtl import *
from tests.context import lizard
from lizard.util.rtl.branch_predictor import BranchPredictorInterface, GlobalBranchPredictor
from lizard.model.translate import translate


def test_translation0():
  iface = BranchPredictorInterface(32, 32)
  model = GlobalBranchPredictor(iface, 0, 0, 0, hasher='xor')
  translate(model)

def test_translation1():
  iface = BranchPredictorInterface(32, 32)
  model = GlobalBranchPredictor(iface, 1, 2, 3, hasher='xor')
  translate(model)
