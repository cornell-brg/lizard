from pymtl import *
import abc
from functools import wraps
from collections import OrderedDict


class EntryGroup(object):
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def size(s):
    pass

  @abc.abstractmethod
  def offsets(s):
    pass


class Field(EntryGroup):

  def __init__(s, name, width):
    s.name = name
    s.width = width

  def size(s):
    return s.width

  def offsets(s):
    yield s.name, 0, s.width

  def __str__(s):
    return '{}[{}]'.format(s.name, s.width)


class Group(EntryGroup):

  def __init__(s, fields):
    s.fields = fields
    s.width = 0
    for field in s.fields:
      s.width += field.size()

  def size(s):
    return s.width

  def offsets(s):
    base = 0
    for field in s.fields:
      for name, offset, size in field.offsets():
        yield name, (offset + base), size
      base += field.size()


class Union(EntryGroup):

  def __init__(s, fields):
    s.fields = fields
    s.width = 0
    for field in s.fields:
      s.width = max(s.width, field.size())

  def size(s):
    return s.width

  def offsets(s):
    for field in s.fields:
      for name, offset, size in field.offsets():
        yield name, offset, size


def bit_struct_generator(func):
  struct_name = func.__name__

  @wraps(func)
  def gen(*args):
    fields = func(*args)
    top = Group(fields)

    class_name = "{}_{}".format(struct_name, '_'.join(str(x) for x in args))
    bitstruct_class = type(class_name, (BitStruct,), {})
    bitstruct_class._bitfields = OrderedDict()

    for name, offset, size in top.offsets():
      # Transform attributes containing BitField objects into properties,
      # when accessed they return slices of the underlying value
      addr = slice(offset, offset + size)
      bitstruct_class._bitfields[name] = addr

      def create_getter(addr):
        return lambda self: self.__getitem__(addr)

      def create_setter(addr):
        return lambda self, value: self.__setitem__(addr, value)

      setattr(bitstruct_class, name,
              property(create_getter(addr), create_setter(addr)))

    def gen_str(s):
      result = [
          '{}={}'.format(name, s[addr].hex())
          for name, addr in bitstruct_class._bitfields.iteritems()
      ]
      return ':'.join(result)

    bitstruct_class.__str__ = gen_str

    bitstruct_inst = bitstruct_class(top.size())

    # hack for verilog translation!
    # These are used in pymtl/tools/translation/cpp_helpers.py
    # They variables below are used to instantiate the given type
    #  elif isinstance( p, InPort ):
    #    if isinstance( p.dtype, BitStruct ):
    #      msg = p.dtype
    #      list_.append( "from {} import {}".format( msg._module, msg._classname ) )
    #      list_.append( "s.{} = InPort( {} )".format( p.name, msg._instantiate ) )
    #    else:
    #      list_.append( "s.{} = InPort( {} )".format( p.name, p.nbits ) )
    #
    #  # TODO: fix msg type
    #  elif isinstance( p, OutPort ):
    #    if isinstance( p.dtype, BitStruct ):
    #      msg = p.dtype
    #      list_.append( "from {} import {}".format( msg._module, msg._classname ) )
    #      list_.append( "s.{} = OutPort( {} )".format( p.name, msg._instantiate ) )
    #    else:
    #      list_.append( "s.{} = OutPort( {} )".format( p.name, p.nbits ) )
    bitstruct_inst._module = func.__module__
    bitstruct_inst._classname = struct_name
    # Note that args is a tuple, so will print with parens around it
    bitstruct_inst._instantiate = '{class_name}{args}'.format(
        class_name=struct_name,
        args=args,
    )

    return bitstruct_inst

  return gen
