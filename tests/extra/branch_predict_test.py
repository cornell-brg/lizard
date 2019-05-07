from pymtl import *
from tests.context import lizard
from lizard.util.rtl.branch_predictor import BranchPredictorInterface, GlobalBranchPredictor
from lizard.model.translate import translate
from lizard.model.wrapper import wrap_to_cl
from lizard.model.hardware_model import not_ready_instance
import csv
import os
import collections

def test_translation0():
  iface = BranchPredictorInterface(32, 32)
  model = GlobalBranchPredictor(iface, 0, 0, 0, hasher='concat')
  translate(model)

def test_translation1():
  iface = BranchPredictorInterface(32, 32)
  model = GlobalBranchPredictor(iface, 1, 2, 3, hasher='xor')
  translate(model)


def test_accuracy0():
  iface = BranchPredictorInterface(32, 4)
  model = translate(GlobalBranchPredictor(iface, 0, 17, 17, hasher='xor'))
  model.vcd_file = 'branch_predictor.vcd'
  df = wrap_to_cl(model)
  df.reset()

  total = 0
  correct = 0
  expected = collections.deque()
  root = os.path.dirname(os.path.abspath(__file__))
  with open(root + "/branch_trace2.csv", 'rb') as fd:
    reader = csv.reader(fd)
    for row in reader:
      total += 1
      pc = int(row[0])
      taken = int(row[1])
      # Make a prediction
      idx = df.predict(pc).idx
      expected.append((idx, taken))
      # This will allow multiple branches in flight at once
      pred = df.prediction()
      if pred != not_ready_instance:
        idx, outcome = expected.popleft()
        if outcome == pred.taken:
          correct += 1
        df.update(idx=idx, taken=outcome)
      df.cycle()

      # pred = None
      # while pred is None or pred == not_ready_instance:
      #   pred = df.prediction()
      #   df.cycle()
      #
      # idx, outcome = expected.popleft()
      # if outcome == pred.taken:
      #   correct += 1
      # df.update(idx=idx, taken=outcome)
      # df.cycle()

      acc = correct / float(total)
      print("num: {}, acc: {}".format(total, acc) )
