from pymtl import *
import imp


def translate_class(model, use_cached_verilated=False):
  result_class = None

  if use_cached_verilated:
    class_name = model._gen_class_name(model)
    python_name = '{}_v.py'.format(class_name)
    try:
      verilated_module = imp.load_source(class_name, python_name)
      result_class = verilated_module.__dict__[class_name]
    except:
      pass

  if result_class is None:
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


def translate(model, use_cached_verilated=False):
  global global_translation_cache

  gen_name = model._gen_class_name(model)
  if gen_name not in global_translation_cache:
    global_translation_cache[gen_name] = translate_class(
        model, use_cached_verilated=use_cached_verilated)

  return global_translation_cache[gen_name]()
