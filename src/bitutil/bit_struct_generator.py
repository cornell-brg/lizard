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

  def __init__(s, *fields):
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

  def __init__(s, *fields):
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


def Field(name, type_):
  if isinstance(type_, int):
    return PrimitiveField(name, type_)
  elif isinstance(type_, BitStruct) and hasattr(type_, '_spec'):
    return Union(
        PrimitiveField(name, type_._spec.size()),
        NestedField(name, type_),
    )
  else:
    print(type_.__dict__)
    raise ValueError('Unknown field type: {}'.format(type(type_)))


evil_hacky_global_type_dictionary = {}
evil_hacky_global_counter = 0


def bit_struct_generator(func):
  struct_name = func.__name__

  @wraps(func)
  def gen(*args):
    top = Group(*func(*args))

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

    def gen_init(s, nbits=top.size()):
      assert nbits == top.size()
      super(bitstruct_class, s).__init__(top.size())
      # save the spec inside all all instances so we can nest
      s._spec = top

    bitstruct_class.__init__ = gen_init
    global evil_hacky_global_type_dictionary
    global evil_hacky_global_counter
    evil_global_id = evil_hacky_global_counter
    evil_hacky_global_type_dictionary[evil_global_id] = bitstruct_class
    evil_hacky_global_counter += 1

    bitstruct_inst = bitstruct_class()

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
    bitstruct_inst._module = __name__
    bitstruct_inst._classname = 'evil_hacky_global_type_dictionary'
    bitstruct_inst._instantiate = 'evil_hacky_global_type_dictionary[{}]()'.format(
        evil_global_id)

    return bitstruct_inst

  return gen
