from pymtl import *


class ValRdyCLPort:

  def __init__(s, data_type):
    s.msg = data_type()
    s.valid = False
    s.mimic = None

  def empty(s):
    if s.mimic:
      return s.mimic.empty()
    return not s.valid

  def full(s):
    if s.mimic:
      return s.mimic.full()
    return s.valid

  def deq(s):
    if s.mimic:
      return s.mimic.deq()
    assert s.full()
    s.valid = False
    return s.msg

  def last(s):
    if s.mimic:
      return s.mimic.last()
    assert s.full()
    return s.msg

  def enq(s, msg):
    if s.mimic:
      s.mimic.enq(msg)
      return
    assert s.empty()
    s.valid = True
    s.msg = msg

  def set_mimic(s, other):
    if s.mimic:
      s.mimic.set_mimic(other)
    else:
      s.mimic = other


class InValRdyCLPort:

  def __init__(s, data_type):
    s.port = None
    s.data_type = data_type

  def empty(s):
    return s.port.empty()

  def deq(s):
    return s.port.deq()

  def peek(s):
    assert not s.empty()
    return s.port.last()


class OutValRdyCLPort:

  def __init__(s, data_type):
    s.port = None
    s.data_type = data_type

  def full(s):
    return s.port.full()

  def enq(s, msg):
    s.port.enq(msg)

  def peek(s):
    assert s.full()
    return s.port.last()

  def msg(s):
    if not s.port.full():
      return s.data_type()
    else:
      return s.port.last()

  def val(s):
    return s.port.full()


def cl_connect(p1, p2):
  assert p1.data_type == p2.data_type

  # if both have ports, pick one as master port
  if p1.port and p2.port:
    p2.port.set_mimic(p1.port)
  elif p1.port:
    p2.port = p1.port
  elif p2.port:
    p1.port = p2.port
  else:
    p1.port = ValRdyCLPort(p1.data_type)
    p2.port = p1.port
