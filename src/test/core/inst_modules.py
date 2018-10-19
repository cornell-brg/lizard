from test.core import inst
import pkgutil
import importlib


def inst_module2s():
  return []


def inst_modules():
  modules = []
  for _, cat, _ in pkgutil.iter_modules( path=inst.__path__ ):
    module = importlib.import_module( inst.__name__ + '.' + cat )
    for _, name, _ in pkgutil.iter_modules( path=module.__path__ ):
      modules += [ importlib.import_module( module.__name__ + '.' + name ) ]
    pass
  return modules


if __name__ == '__main__':
  print inst_modules()
