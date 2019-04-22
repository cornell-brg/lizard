import abc
from functools import wraps
from collections import OrderedDict
from pymtl import *
from lizard.bitutil import slice_len


def _escape(string):
  return string.replace('_', '__')


class EntryGroup(object):
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def size(s):
    pass

  @abc.abstractmethod
  def offsets(s):
    pass

  def export(s):
    return s.size(), list(s.offsets())

  def canonical_name(s):
    parts = sorted([
        '{}_{}_{}'.format(_escape(name), offset, size)
        for name, offset, size in s.offsets()
    ])
    return '{}_{}'.format(s.size(), '_'.join(parts))


class PrimitiveField(EntryGroup):

  def __init__(s, name, width):
    s.name = name
    s.width = width

  def size(s):
    return s.width

  def offsets(s):
    yield s.name, 0, s.width

  def __str__(s):
    return '{}[{}]'.format(s.name, s.width)


class NestedField(EntryGroup):

  def __init__(s, name, type_):
    assert isinstance(type_, BitStruct) and hasattr(type_, '_spec')

    s.name = name
    s.type_ = type_._spec
    s.width = s.type_.size()

  def size(s):
    return s.width

  def offsets(s):
    # name mangle since this is nested
    for name, offset, size in s.type_.offsets():
      yield '{}_{}'.format(s.name, name), offset, size


class Group(EntryGroup):

  def __init__(s, name, *fields):
    s.name = name
    s.fields = fields
    s.width = 0
    for field in s.fields:
      s.width += field.size()

  def size(s):
    return s.width

  def offsets(s):
    base = 0
    if s.name is not None:
      yield s.name, 0, s.size()
    for field in s.fields:
      for name, offset, size in field.offsets():
        yield name, (offset + base), size
      base += field.size()


def Inline(name, type_):
  # the spec for a full type is always a group, so just take the fields
  return Group(name, *type_._spec.fields)


class Union(EntryGroup):

  def __init__(s, name, *fields):
    s.name = name
    s.fields = fields
    s.width = 0
    for field in s.fields:
      s.width = max(s.width, field.size())

  def size(s):
    return s.width

  def offsets(s):
    if s.name is not None:
      yield s.name, 0, s.size()
    for field in s.fields:
      for name, offset, size in field.offsets():
        yield name, offset, size


class ExplicitStructDefinition(EntryGroup):

  def __init__(s, width, field_spec):
    s.field_spec = field_spec
    s.width = width

  def size(s):
    return s.width

  def offsets(s):
    return s.field_spec


def Field(name, type_):
  if isinstance(type_, int):
    return PrimitiveField(name, type_)
  elif isinstance(type_, BitStruct) and hasattr(type_, '_spec'):
    return Union(
        name,
        NestedField(name, type_),
    )
  else:
    raise ValueError('Unknown field type: {}'.format(type(type_)))


def SlicedStruct(width, **kwargs):
  return ExplicitStructDefinition(width,
                                  [(name, slice_.start, slice_len(slice_))
                                   for name, slice_ in kwargs.iteritems()])


def bit_struct_generator(func):
  struct_name = func.__name__

  @wraps(func)
  def gen(*args):
    gen = func(*args)
    if isinstance(gen, EntryGroup):
      top = gen
    else:
      top = Group(None, *gen)

    class_name = "{}_{}".format(_escape(struct_name), top.canonical_name())
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

    def gen_init(s, nbits=top.size()):
      assert nbits == top.size()
      super(bitstruct_class, s).__init__(top.size())
      # save the spec inside all all instances so we can nest
      s._spec = top
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
      #  # TQDO: fix msg type
      #  elif isinstance( p, OutPort ):
      #    if isinstance( p.dtype, BitStruct ):
      #      msg = p.dtype
      #      list_.append( "from {} import {}".format( msg._module, msg._classname ) )
      #      list_.append( "s.{} = OutPort( {} )".format( p.name, msg._instantiate ) )
      #    else:
      #      list_.append( "s.{} = OutPort( {} )".format( p.name, p.nbits ) )
      s._module = __name__
      s._classname = '_regen_type'
      # top.export() returns a tuple which will have parens around it
      s._instantiate = '_regen_type({})'.format(top.export())

    bitstruct_class.__init__ = gen_init

    bitstruct_inst = bitstruct_class()

    return bitstruct_inst

  return gen


@bit_struct_generator
def _regen_type(full_spec):
  return ExplicitStructDefinition(*full_spec)
