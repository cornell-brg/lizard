import os
import sys

lizard_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..')

try:
  import lizard
except ImportError:
  sys.path.insert(0, lizard_dir)
  import lizard
