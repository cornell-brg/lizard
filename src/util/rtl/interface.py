from collections import OrderedDict
from pytml import *
from util.rtl.method import MethodSpec

class Interface(object):
  def __init__(s):
    s.methods = OrderedDict()

  def add_method(s, name, args, rets, has_call, has_rdy, count=None):
    if name in s.methods:
      raise ValueError('Method already exists: {}'.format(name))
    s.methods[name] = (MethodSpec(args, rets, has_call, has_rdy), count)

  def inject(s, target, prefix, name, spec, count, direction):
    if count is None:
      port_map = spec.generate(direction)
    else:
      ports = [spec.generate(MethodSpec.DIRECTION_IN) for _ in range(count)]
      port_map = {}
      for port_name in spec.ports():
        port_map[port_name] = [ports[i][port_name] for i in range(count)]
    
    for port_name, port in ports.iteritems():
      setattr(target, '{}{}_{}'.format(prefix, name, port_name), port)

  def apply(s, target):
    for name, method in s.methods.iteritems():
      spec, count = method
      s.inject(target, '', name, spec, count, MethodSpec.DIRECTION_IN)

  def require(s, target, prefix, name, count=None):
    if len(prefix) > 0:
      prefix = '{}_'.format(prefix)
    
    spec, available = s.methods[name]
    # Should be possible to prevent over-allocation
    # if available is None and count is None:
    #   pass
    # elif available is not None and count is None:
    #   available -= 1
    # elif count <= available:
    #   available -= count
    # else:
    #   raise ValueError('No more ports for method left: {}'.format(name))
    s.inject(target, prefix, name, spec, count, MethodSpec.DIRECTION_OUT)

