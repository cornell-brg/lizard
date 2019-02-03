from inspect import isclass
from pymtl import *
from model.flmodel import FLModel
from model.clmodel import CLModel
from model.rtlwrapper import RTLWrapper
from model.clwrapper import CLWrapper
from model.fladapter import FLAdapter
from model.cladapter import CLAdapter


class Wrapper(object):

  def __init__(s, wrapped, wrapping):
    s.wrapped = wrapped
    s.wrapping = wrapping

  def __call__(s, *args, **kwargs):
    if isclass(s.wrapped) or isinstance(s.wrapped, Wrapper):
      inside = s.wrapped(*args, **kwargs)
    else:
      inside = s.wrapped
    return s.wrapping(inside)


def class_type(obj):
  if isclass(obj):
    return obj
  else:
    return type(obj)


def wrap(model, wrap_spec):
  model_type = class_type(model)
  result = model
  for layer in wrap_spec:
    result = Wrapper(result, layer)

  # if the input was not a class, evaluate it
  # make sure we actually wrapped it as well
  if not isclass(model) and isinstance(result, Wrapper):
    result = result()

  return result


def gen_wrap(wrap_spec):

  def do_wrap(model):
    model_type = class_type(model)
    for target_type, spec in wrap_spec.iteritems():
      if issubclass(model_type, target_type):
        return wrap(model, spec)
    raise ValueError('Unable to wrap type: {}'.format(model_type))

  return do_wrap


wrap_to_rtl = gen_wrap({
    Model: [],
    CLModel: [CLAdapter],
    FLModel: [FLAdapter, CLAdapter],
})

wrap_to_cl = gen_wrap({
    Model: [RTLWrapper],
    CLModel: [],
    FLModel: [FLAdapter],
})

wrap_to_fl = gen_wrap({
    Model: [RTLWrapper, CLWrapper],
    CLModel: [CLWrapper],
    FLModel: [],
})
