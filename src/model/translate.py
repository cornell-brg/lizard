from pymtl import *


def translate(model):
  result = TranslationTool(model, lint=True)
  model.interface.embed(result)
  return result
