from pymtl import *


def translate_class(model):
  result_model = TranslationTool(model, lint=True)
  # Generated moodel has this code:
  # def __del__( s ):
  #   s._ffi.destroy_model( s._m )
  # This means it can't be destroyed before it's been elaborated
  # or a strange message is printed:
  # Exception AttributeError: "'Proc_0x61a5b3756704d9a6' object has no attribute
  # '_m'" in <bound method Proc_0x61a5b3756704d9a6.__del__ of
  # <Proc_0x61a5b3756704d9a6_v.Proc_0x61a5b3756704d9a6 object at
  # 0x7fd465eb5350>> ignored
  # So:
  # 1) Elaborate result_model to avoid that
  # 2) Monkey patch the class to fix this behavior
  result_class = result_model.__class__

  result_model.elaborate_logic()
  result_class._old_del = result_class.__del__

  def sane_del(s):
    if hasattr(s, '_m'):
      s._old_del()

  result_class.__del__ = sane_del

  # Monkey patch init such that each instantiation of the translated
  # model has an interface inside
  def embed_init(s, *args, **kwargs):
    s._old_init(*args, **kwargs)
    model.interface.embed(s, model._requirements)

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
