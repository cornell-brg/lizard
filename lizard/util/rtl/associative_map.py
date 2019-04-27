from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type, Array
from lizard.util.rtl.register import Register, RegisterInterface
from lizard.util.rtl.sync_ram import SynchronousRAMInterface, SynchronousRAM
from lizard.util.rtl.packers import Packer, Unpacker
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

  def __init__(s, Data, n):
    s.Data = canonicalize_type(Data)
    s.Index = clog2nz(n)
    super(EvictorInterface, s).__init__([
        MethodSpec(
            'evict',
            args={
                'valid': Array(Bits(1), n),
                'data': Array(s.Data, n),
            },
            rets={
                'index': s.Index,
            },
            call=True,
            rdy=False,
        ),
    ])


class LineReaderInterface(Interface):

  def __init__(s, Key, Data, n):
    s.Key = canonicalize_type(Key)
    s.Data = canonicalize_type(Data)
    s.Index = clog2nz(n)
    super(LineReaderInterface, s).__init__([
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
    ])


class LineWriterInterface(Interface):

  def __init__(s, Key, Data, n):
    s.Key = canonicalize_type(Key)
    s.Data = canonicalize_type(Data)
    s.Index = clog2nz(n)
    super(LineWriterInterface, s).__init__([
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
            'write',
            args={
                'key': s.Key,
                'data': s.Data,
                'remove': Bits(1),
            },
            rets={
                'found': Bits(1),
                'old': s.Data,
            },
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'out',
            args=None,
            rets={
                'valid': Array(Bits(1), n),
                'keys': Array(s.Key, n),
                'data': Array(s.Data, n),
            },
            call=False,
            rdy=False,
        ),
    ])


class UpdaterInterface(Interface):

  def __init__(s, Data):
    s.Data = canonicalize_type(Data)
    super(UpdaterInterface, s).__init__([
        MethodSpec(
            'update',
            args={
                'found': Bits(1),
                'old': s.Data,
            },
            rets={
                'new': s.Data,
                'remove': Bits(1),
            },
            call=False,
            rdy=False,
        )
    ])


class Searcher(Model):

  def __init__(s, Key, n):
    UseInterface(s, SearcherInterface(Key, n))

    s.valid_chain = [Wire(1) for _ in range(n + 1)]
    s.index_chain = [Wire(s.interface.Index) for _ in range(n + 1)]

    @s.combinational
    def chain_0():
      s.valid_chain[0].v = 0
      s.index_chain[0].v = 0

    for i in range(n):

      @s.combinational
      def chain(i=i, j=i + 1):
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

    s.counter = Register(
        RegisterInterface(s.interface.Index, enable=True), reset_value=0)
    s.invalid_finder = Searcher(Bits(1), n)
    for i in range(n):
      s.connect(s.invalid_finder.find_valid[i], 1)
      s.connect(s.invalid_finder.find_keys[i], s.evict_valid[i])
    s.connect(s.invalid_finder.find_target, 0)

    @s.combinational
    def evict(nm1=n - 1):
      if s.counter.read_data == nm1:
        s.counter.write_data.v = 0
      else:
        s.counter.write_data.v = s.counter.read_data + 1
      s.counter.write_call.v = s.invalid_finder.find_found

      if s.invalid_finder.find_found:
        s.evict_index.v = s.invalid_finder.find_index
      else:
        s.evict_index.v = s.counter.read_data


class LineReader(Model):

  def __init__(s, Key, Data, n):
    UseInterface(s, LineReaderInterface(Key, Data, n))
    s.read_searcher = Searcher(Key, n)

    for i in range(n):
      s.connect(s.read_searcher.find_valid[i], s.in__valid[i])
      s.connect(s.read_searcher.find_keys[i], s.in__keys[i])

    s.connect(s.read_searcher.find_target, s.read_key)
    s.connect(s.read_found, s.read_searcher.find_found)

    @s.combinational
    def read():
      s.read_data.v = s.in__data[s.read_searcher.find_index]


class LineWriter(Model):

  def __init__(s, Key, Data, n):
    UseInterface(s, LineWriterInterface(Key, Data, n))
    s.write_searcher = Searcher(Key, n)
    s.evictor = IncrementingEvictor(Data, n)

    for i in range(n):
      s.connect(s.write_searcher.find_valid[i], s.in__valid[i])
      s.connect(s.write_searcher.find_keys[i], s.in__keys[i])
      s.connect(s.evictor.evict_valid[i], s.in__valid[i])

    s.connect(s.write_searcher.find_target, s.write_key)
    s.connect(s.write_found, s.write_searcher.find_found)

    @s.combinational
    def old():
      s.write_old.v = s.in__data[s.write_searcher.find_index]

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

      @s.combinational
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

  def __init__(s, Key, Data, has_update):
    s.Key = canonicalize_type(Key)
    s.Data = canonicalize_type(Data)

    def add_update(spec):
      if has_update:
        spec['update'] = Bits(1)
      return spec

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
            args=add_update({
                'key': s.Key,
                'remove': Bits(1),
                'data': s.Data,
            }),
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


class GeneralAssociativeMap(Model):

  def __init__(s, Key, Data, capacity, associativity):
    UseInterface(s, AssociativeMapInterface(Key, Data, True))
    s.require(
        MethodSpec(
            'update',
            args={
                'found': Bits(1),
                'old': Data,
            },
            rets={
                'new': Data,
                'remove': Bits(1),
            },
            call=False,
            rdy=False,
        ),)

    nlines = capacity // associativity
    assert capacity % associativity == 0
    high_nbits = clog2(nlines)
    assert 2**high_nbits == nlines
    key_nbits = Key.nbits
    low_nbits = key_nbits - high_nbits

    state = 'n'
    if low_nbits == 0:
      # For a direct-mapped map with no low bits
      # pretend there is one so we don't have zero width signals
      low_nbits = 1
      state = 'd'
    if high_nbits == 0:
      # For a fully associative map we need 1 high bit to represent address 0
      # in the ram
      high_nbits = 1
      state = 'f'

    @bit_struct_generator
    def Entry():
      return [
          Field('key', low_nbits),
          Field('data', Data),
      ]

    entry_nbits = Entry().nbits
    line_nbits = entry_nbits * associativity

    s.read_next_key_high = Wire(high_nbits)
    s.read_next_key_low = Wire(low_nbits)
    s.write_key_high = Wire(high_nbits)
    s.write_key_low = Wire(low_nbits)
    if state == 'f':
      s.connect(s.read_next_key_high, 0)
      s.connect(s.write_key_high, 0)
    else:
      s.connect(s.read_next_key_high, s.read_next_key[low_nbits:key_nbits])
      s.connect(s.write_key_high, s.write_key[low_nbits:key_nbits])
    if state == 'd':
      s.connect(s.read_next_key_low, 0)
      s.connect(s.write_key_low, 0)
    else:
      s.connect(s.read_next_key_low, s.read_next_key[0:low_nbits])
      s.connect(s.write_key_low, s.write_key[0:low_nbits])

    # Writes to the RAM must be bypassed to support 2 consecutive calls to "write" (on this map) (MW)
    # This is because a write takes 2 cycles: Read Request (R), Read Response and Write (W)
    # So assume 2 map writes occur right after each other:
    # Op | 0 | 1 | 2 | 3 | 4 |
    # ---|---|---|---|---|---|
    # MW | R | W |   |   |   |
    # MW |   | R | W |   |   |
    # The write in column 1 must forward its data to the read that cycle.
    s.ram = SynchronousRAM(
        SynchronousRAMInterface(line_nbits, nlines, 2, 1, True))
    s.valids = [
        Register(
            RegisterInterface(Bits(associativity), enable=True), reset_value=0)
        for _ in range(nlines)
    ]
    s.line_reader = LineReader(low_nbits, Data, associativity)
    s.line_writer = LineWriter(low_nbits, Data, associativity)
    s.read_unpacker = Unpacker(Entry(), associativity)
    s.write_unpacker = Unpacker(Entry(), associativity)
    s.write_packer = Packer(Entry(), associativity)

    s.read_next_key_high_reg = Register(RegisterInterface(high_nbits))
    s.read_next_key_low_reg = Register(RegisterInterface(low_nbits))
    s.write_key_reg_high = Register(RegisterInterface(high_nbits))
    s.write_key_reg_low = Register(RegisterInterface(low_nbits))
    s.write_remove_reg = Register(RegisterInterface(Bits(1)))
    s.write_update_reg = Register(RegisterInterface(Bits(1)))
    s.write_data_reg = Register(RegisterInterface(Data))
    s.write_call_reg = Register(RegisterInterface(Bits(1)), reset_value=0)

    s.connect(s.read_next_key_high_reg.write_data, s.read_next_key_high)
    s.connect(s.read_next_key_low_reg.write_data, s.read_next_key_low)
    s.connect(s.write_key_reg_high.write_data, s.write_key_high)
    s.connect(s.write_key_reg_low.write_data, s.write_key_low)
    s.connect(s.write_remove_reg.write_data, s.write_remove)
    s.connect(s.write_update_reg.write_data, s.write_update)
    s.connect(s.write_data_reg.write_data, s.write_data)

    s.connect(s.update_found, s.line_writer.write_found)
    s.connect(s.update_old, s.line_writer.write_old)

    @s.combinational
    def handle_write_clear():
      # If a clear is going to happen do not do the write
      s.write_call_reg.write_data.v = s.write_call and not s.clear_call

    s.connect(s.ram.read_next_addr[0], s.read_next_key_high_reg.read_data)
    s.connect(s.read_unpacker.unpack_packed, s.ram.read_data[0])
    s.connect(s.ram.read_next_addr[1], s.write_key_high)
    s.connect(s.write_unpacker.unpack_packed, s.ram.read_data[1])
    s.connect(s.ram.write_data[0], s.write_packer.pack_packed)

    for i in range(associativity):
      s.connect(s.line_reader.in__keys[i], s.read_unpacker.unpack_out[i].key)
      s.connect(s.line_reader.in__data[i], s.read_unpacker.unpack_out[i].data)

      s.connect(s.line_writer.in__keys[i], s.write_unpacker.unpack_out[i].key)
      s.connect(s.line_writer.in__data[i], s.write_unpacker.unpack_out[i].data)

      s.connect(s.write_packer.pack_in_[i].key, s.line_writer.out_keys[i])
      s.connect(s.write_packer.pack_in_[i].data, s.line_writer.out_data[i])

      @s.combinational
      def connect_in_valids(i=i):
        s.line_reader.in__valid[i].v = s.valids[s.read_next_key_high_reg
                                                .read_data].read_data[i]
        s.line_writer.in__valid[i].v = s.valids[s.write_key_high].read_data[i]

    for j in range(nlines):

      @s.combinational
      def handle_valids_write_call(j=j):
        s.valids[j].write_call.v = (
            s.write_call_reg.read_data and
            s.write_key_reg_high.read_data == j) or s.clear_call

      for i in range(associativity):

        @s.combinational
        def connect_out_valids(i=i, j=j):
          if s.clear_call:
            s.valids[j].write_data[i].v = 0
          else:
            s.valids[j].write_data[i].v = s.line_writer.out_valid[i]

    s.connect(s.line_reader.read_key, s.read_next_key_low_reg.read_data)
    s.connect(s.read_data, s.line_reader.read_data)
    s.connect(s.read_found, s.line_reader.read_found)

    s.connect(s.line_writer.write_key, s.write_key_reg_low.read_data)

    @s.combinational
    def handle_write_update():
      if s.write_update_reg.read_data:
        s.line_writer.write_data.v = s.update_new
        s.line_writer.write_remove.v = s.update_remove
      else:
        s.line_writer.write_data.v = s.write_data_reg.read_data
        s.line_writer.write_remove.v = s.write_remove_reg.read_data

    s.connect(s.line_writer.write_call, s.write_call_reg.read_data)
    s.connect(s.ram.write_call[0], s.write_call_reg.read_data)


class NullUpdater(Model):

  def __init__(s, Data):
    UseInterface(s, UpdaterInterface(Data))

    s.connect(s.update_new, 0)
    s.connect(s.update_remove, 0)


class BasicAssociativeMap(Model):

  def __init__(s, Key, Data, capacity, associativity):
    UseInterface(s, AssociativeMapInterface(Key, Data, False))

    s.map = GeneralAssociativeMap(Key, Data, capacity, associativity)
    s.updater = NullUpdater(Data)
    s.connect_m(s.map.read, s.read)
    s.connect_m(s.map.read_next, s.read_next)
    s.connect(s.map.write_key, s.write_key)
    s.connect(s.map.write_remove, s.write_remove)
    s.connect(s.map.write_data, s.write_data)
    s.connect(s.map.write_call, s.write_call)
    s.connect(s.map.write_update, 0)
    s.connect_m(s.map.clear, s.clear)
    s.connect_m(s.map.update, s.updater.update)
