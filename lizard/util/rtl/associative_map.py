from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type, Array
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.async_ram import AsynchronousRAMInterface, AsynchronousRAM
from lizard.bitutil.bit_struct_generator import *
from lizard.bitutil import clog2nz

class SearcherInterface(Interface):
  def __init__(s, Key, n):
    s.Key = canonicalize_type(Key)
    s.Index = clog2nz(n)
    super(SearcherInterface, s).__init__([
      MethodSpec(
        'find',
        args={
          'valid': Array(Bits(1), n),
          'keys': Array(s.Key, n),
          'target': s.Key,
        },
        rets={
          'index': s.Index,
          'found': Bits(1),
        },
        call=False,
        rdy=False,
      ),
    ])

class EvictorInterface(Interface):
  def __init__(s, n):
    s.Index = clog2nz(n)
    super(EvictorInterface, s).__init__([
      MethodSpec(
        'evict',
        args={
          'valid': Array(Bits(1), n),
        },
        rets={
          'index': s.Index,
        },
        call=True,
        rdy=False,
      ),
    ])


class LookupLineInterface(Interface):
  def __init__(s, Key, Data, n):
    s.Key = canonicalize_type(Key)
    s.Data = canonicalize_type(Data)
    s.Index = clog2nz(n)
    super(LookupLineInterface, s).__init__([
      MethodSpec(
        'in_',
        args={
          'valid': Array(Bits(1), n),
          'keys': Array(s.Key, n),
          'data': Array(s.Data, n),
        },
        rets=None,
        call=False,
        rdy=False,
      ),
      MethodSpec(
        'read',
        args={
          'key': s.Key,
        },
        rets={
          'data': s.Data,
          'found': Bits(1),
        },
        call=False,
        rdy=False,
      ),
      MethodSpec(
        'write',
        args={
          'key': s.Key,
          'data': s.Data,
          'remove': Bits(1),
        },
        rets={
          'found': Bits(1),
        },
        call=True,
        rdy=False,
      ),
      MethodSpec(
        'out',
        args={
          'valid': Array(Bits(1), n),
          'keys': Array(s.Key, n),
          'data': Array(s.Data, n),
        },
        rets=None,
        call=False,
        rdy=False,
      ),
    ])

class Searcher(Model):
  def __init__(s, Key, n):
    UseInterface(s, SearcherInterface(Key, n))

    s.valid_chain = [Wire(1) for _ in range(n+1)]
    s.index_chain = [Wire(s.interface.Index) for _ in range(n+1)]

    @s.combinational
    def chain_0():
      s.valid_chain[0].v = 0
      s.index_chain[0].v = 0

    for i in range(n):
      @s.combinational
      def chain(i=i, j=i+1):
        if s.find_valid[i] and s.find_keys[i] == s.find_target:
          s.valid_chain[j].v = 1
          s.index_chain[j].v = i
        else:
          s.valid_chain[j].v = s.valid_chain[i]
          s.index_chain[j].v = s.index_chain[i]

    s.connect(s.find_found, s.valid_chain[-1])
    s.connect(s.find_index, s.index_chain[-1])

class IncrementingEvictor(Model):
  def __init__(s, Data, n):
    UseInterface(s, EvictorInterface(Data, n))

    s.counter = Register(RegisterInterface(s.interface.Index, enable=True), reset_value=0)
    s.invalid_finder = Searcher(s, Bits(1), n)
    for i in range(n):
      s.connect(s.invalid_finder.find_valid[i], 1)
      s.connect(s.invalid_finder.find_keys[i], s.evict_valid[i])
    s.connect(s.invalid_finder.evict_target, 0)

    @s.combinational
    def evict(nm1=n-1):
      if s.counter.read_data == nm1:
        s.counter.write_data.v = 0
      else:
        s.counter.write_data.v = s.counter.read_data + 1
      s.counter.write_call.v = s.invalid_finder.find_found
      
      if s.invalid_finder.find_found:
        s.evict_index.v = s.invalid_finder.find_index
      else:
        s.evict_index.v = s.counter.read_data

class LookupLine(Model):
  def __init__(s, Key, Data, n):
    UseInterface(s, LookupLineInterface(Key, Data, n))
    s.read_searcher = Searcher(Key, n)
    s.write_searcher = Searcher(Key, n)
    s.evictor = IncrementingEvictor(n)

    for i in range(n):
      s.connect(s.read_searcher.find_valid[i], s.in__valid[i])
      s.connect(s.read_searcher.find_keys[i], s.in__keys[i])
      s.connect(s.write_searcher.find_valid[i], s.in__valid[i])
      s.connect(s.write_searcher.find_keys[i], s.in__keys[i])
      s.connect(s.evictor.evict_valid[i], s.in__valid[i])

    s.connect(s.read_searcher.find_target, s.read_key)
    s.connect(s.write_searcher.find_target, s.write_key)
    s.connect(s.read_found, s.read_searcher.find_found)
    s.connect(s.write_found, s.write_searcher.find_found)

    @s.combinational
    def read():
      s.read_data.v = s.in__data[s.read_searcher.find_index]
    
    s.write_index = Wire(s.interface.Index)

    @s.combinational
    def compute_write_index():
      if s.write_searcher.find_found:
        s.write_index.v = s.write_searcher.find_index
        s.evictor.evict_call.v = 0
      else:
        s.write_index.v = s.evictor.evict_index
        s.evictor.evict_call.v = s.write_call and not s.write_remove

    for i in range(n):
      def out(i=i):
        if s.write_call:
          if s.write_remove:
            if s.write_searcher.find_found and s.write_searcher.find_index == i:
              s.out_valid[i].v = 0
              s.out_keys[i].v = 0
              s.out_data[i].v = 0
            else:
              s.out_valid[i].v = s.in__valid[i]
              s.out_keys[i].v = s.in__keys[i]
              s.out_data[i].v = s.in__data[i]
          elif s.write_index == i:
            s.out_valid[i].v = 1
            s.out_keys[i].v = s.write_key
            s.out_data[i].v = s.write_data
          else:
            s.out_valid[i].v = s.in__valid[i]
            s.out_keys[i].v = s.in__keys[i]
            s.out_data[i].v = s.in__data[i]
        else:
          s.out_valid[i].v = s.in__valid[i]
          s.out_keys[i].v = s.in__keys[i]
          s.out_data[i].v = s.in__data[i]

class AssociativeMapInterface(Interface):
  def __init__(s, Key, Data):
    s.Key = canonicalize_type(Key)
    s.Data = canonicalize_type(Data)

    super(AssociativeMapInterface, s).__init__([
        MethodSpec(
            'read',
            args=None,
            rets={
                'data': s.Data,
                'found': Bits(1)
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'read_next',
            args={
                'key': s.Key,
            },
            rets=None,
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'write',
            args={
                'key': s.Key,
                'remove': Bits(1),
                'data': s.Data,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'clear',
            args=None,
            rets=None,
            call=True,
            rdy=False,
        ),
    ])

class AssociativeMap(Model):
  def __init__(s, Key, Data, capacity, associativity):
    UseInterface(s, AssociativeMapInterface(Key, Data))

    @bit_struct_generator
    def Entry():
      return [
          Field('key', Key),
          Field('data', Data),
          Field('valid', 1),
        ]

    entry_nbits = Entry().nbits
    nlines = capacity // associativity
    assert capacity % associativity == 0
    # s.ram = AsynchronousRAM(AsynchronousRAMInterface(entry_nbits, nlines, 2



