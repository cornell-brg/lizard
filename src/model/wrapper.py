from pymtl import *
from model.flmodel import FLModel
from model.rtlwrapper import RTLWrapper
from model.clmodel import CLModel


def wrap_to_cl(model):
  if isinstance(model, CLModel):
    return model
  elif isinstance(model, Model):
    return RTLWrapper(model)
  elif isinstance(model, FLModel):
    return model
  else:
    raise ValueError('Unknown model type: {}'.format(type(model)))
