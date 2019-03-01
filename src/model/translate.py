from pymtl import *


def translate_class(model):
  result_class = TranslationTool(model, lint=True).__class__

  # Monkey patch init such that each instantiation of the translated
  # model has an interface inside
  # Also copy over the VCD file name
  def embed_init(s, *args, **kwargs):
    s._old_init(*args, **kwargs)
    model.interface.embed(s, model._requirements)
    if hasattr(model, 'vcd_file'):
      s.vcd_file = model.vcd_file

  result_class._old_init = result_class.__init__
  result_class.__init__ = embed_init

  return result_class


global_translation_cache = {}


def translate(model):
  global global_translation_cache

  gen_name = model._gen_class_name(model)
  if gen_name not in global_translation_cache:
    global_translation_cache[gen_name] = translate_class(model)

  return global_translation_cache[gen_name]()
