from pymtl import *
from util.cl.ports import InValRdyCLPort, OutValRdyCLPort


class InValRdyCLPortGroup:

  def __init__(s, ports):
    assert len(ports) >= 1
    s.data_type = ports[0].data_type
    for out_port in ports:
      assert s.data_type == out_port.data_type
    s.ports = ports

  def empty(s):
    # full if any ports are full:
    for port in s.ports:
      if not port.empty():
        return False
    return True

  def get(s, idx):
    return s.ports[idx]

  def deq(s):
    for idx, port in enumerate(s.ports):
      if not port.empty():
        return port.deq(), idx
    assert False


class OutValRdyCLPortGroup:

  def __init__(s, ports):
    assert len(ports) >= 1
    s.data_type = ports[0].data_type
    for out_port in ports:
      assert s.data_type == out_port.data_type
    s.ports = ports

  def full(s):
    # full if any ports are full:
    for port in s.ports:
      if port.full():
        return True
    return False

  def get(s, idx):
    return s.ports[idx]

  def enq(s, msg, idx):
    s.ports[idx].enq(msg)

  def msg(s):
    for port in s.ports:
      if port.full():
        return port.msg()
    return s.data_type()

  def val(s):
    return s.full()
