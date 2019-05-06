from pymtl import *
from tests.context import lizard
from lizard.util.rtl.branch_predictor import BranchPredictorInterface, GlobalBranchPredictor
from lizard.model.translate import translate


def test_translation():
  iface = BranchPredictorInterface(32, 32)
  model = GlobalBranchPredictor(iface, 2, 2, 4, hasher='concat')
  translate(model)
