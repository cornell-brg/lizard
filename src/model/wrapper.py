from pymtl import *
from model.flmodel import FLModel
from model.clmodel import CLModel
from model.rtlwrapper import RTLWrapper
from model.clwrapper import CLWrapper
from model.fladapter import FLAdapter
from model.cladapter import CLAdapter


def wrap_to_rtl(model):
  if isinstance(model, Model):
    return model
  elif isinstance(model, CLModel):
    return CLAdapter(model)
  elif isinstance(model, FLModel):
    return CLAdapter(FLAdapter(model))
  else:
    raise ValueError('Unknown model type: {}'.format(type(model)))


def wrap_to_cl(model):
  if isinstance(model, Model):
    return RTLWrapper(model)
  elif isinstance(model, CLModel):
    return model
  elif isinstance(model, FLModel):
    return FLAdapter(model)
  else:
    raise ValueError('Unknown model type: {}'.format(type(model)))


def wrap_to_fl(model):
  if isinstance(model, Model):
    return CLWrapper(RTLWrapper(model))
  elif isinstance(model, CLModel):
    return CLWrapper(model)
  elif isinstance(model, FLModel):
    return model
  else:
    raise ValueError('Unknown model type: {}'.format(type(model)))
