from pymtl import *
from bitutil import clog2, clog2nz
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from bitutil.bit_struct_generator import *
from util.rtl.register import Register, RegisterInterface


class CAMInterface(Interface):

  def __init__(s, Key, Value, nregs):
    s.nregs = nregs
    s.Addr = Bits(clog2nz(nregs))
    s.Key = canonicalize_type(Key)
    s.Value = canonicalize_type(Value)

    super(CAMInterface, s).__init__([
        MethodSpec(
            'read',
            args={
                'key': s.Key,
            },
            rets={
                'value': s.Value,
                'valid': Bits(1)
            },
            call=False,
            rdy=False,
        ),
        MethodSpec(
            'write',
            args={
                'key': s.Key,
                'remove': Bits(1),
                'value': s.Value,
            },
            rets=None,
            call=True,
            rdy=False,
        ),
    ])


@bit_struct_generator
def Entry(Key, Value):
  return [
      Field('key', Key.nbits),
      Field('value', Value.nbits),
      Field('valid', 1),
  ]


class RandomReplacementCAM(Model):

  def __init__(s, interface):
    UseInterface(s, interface)

    nregs = s.interface.nregs
    Addr = s.interface.Addr
    Key = s.interface.Key
    Value = s.interface.Value

    s.Entry = Entry(Key, Value)
    s.entries = [
        Register(RegisterInterface(s.Entry(), enable=True), reset_value=0)
        for _ in range(nregs)
    ]
    s.overwrite_counter = Register(
        RegisterInterface(Addr, enable=True), reset_value=0)
    s.read_addr_chain = [Wire(Addr) for _ in range(nregs)]
    s.read_addr_valid = [Wire(1) for _ in range(nregs)]

    # PYMTL_BROKEN
    s.entries_read_data_key = [Wire(Key) for _ in range(nregs)]
    s.entries_read_data_value = [Wire(Value) for _ in range(nregs)]
    s.entries_read_data_valid = [Wire(1) for _ in range(nregs)]
    s.entries_write_data_key = [Wire(Key) for _ in range(nregs)]
    s.entries_write_data_value = [Wire(Value) for _ in range(nregs)]
    s.entries_write_data_valid = [Wire(1) for _ in range(nregs)]
    for i in range(nregs):
      s.connect(s.entries_read_data_key[i], s.entries[i].read_data.key)
      s.connect(s.entries_read_data_value[i], s.entries[i].read_data.value)
      s.connect(s.entries_read_data_valid[i], s.entries[i].read_data.valid)
      s.connect(s.entries[i].write_data.key, s.entries_write_data_key[i])
      s.connect(s.entries[i].write_data.value, s.entries_write_data_value[i])
      s.connect(s.entries[i].write_data.valid, s.entries_write_data_valid[i])

    for i in range(nregs):
      if i == 0:

        @s.combinational
        def handle_read_addr_0(i=i):
          s.read_addr_chain[i].v = i
          s.read_addr_valid[i].v = s.entries_read_data_key[
              i] == s.read_key and s.entries_read_data_valid[i]
      else:

        @s.combinational
        def handle_read_addr(i=i, j=i - 1):
          if s.entries_read_data_key[
              i] == s.read_key and s.entries_read_data_valid[i]:
            s.read_addr_chain[i].v = i
            s.read_addr_valid[i].v = 1
          else:
            s.read_addr_chain[i].v = s.read_addr_chain[j]
            s.read_addr_valid[i].v = s.read_addr_valid[j]

    @s.combinational
    def handle_read():
      s.read_value.v = s.entries_read_data_value[s.read_addr_chain[nregs - 1]]
      s.read_valid.v = s.read_addr_valid[nregs - 1]

    s.write_addr_chain = [Wire(Addr) for _ in range(nregs)]
    s.write_addr_valid = [Wire(1) for _ in range(nregs)]
    s.invalid_addr_chain = [Wire(Addr) for _ in range(nregs)]
    s.invalid_addr_valid = [Wire(1) for _ in range(nregs)]

    for i in range(nregs):
      if i == 0:

        @s.combinational
        def handle_write_addr_0(i=i):
          s.write_addr_chain[i].v = i
          s.write_addr_valid[i].v = s.entries_read_data_key[
              i] == s.write_key and s.entries_read_data_valid[i]
          s.invalid_addr_chain[i].v = i
          s.invalid_addr_valid[i].v = not s.entries_read_data_valid[i]
      else:

        @s.combinational
        def handle_write_addr(i=i, j=i - 1):
          if s.entries_read_data_key[
              i] == s.write_key and s.entries_read_data_valid[i]:
            s.write_addr_chain[i].v = i
            s.write_addr_valid[i].v = 1
          else:
            s.write_addr_chain[i].v = s.write_addr_chain[j]
            s.write_addr_valid[i].v = s.write_addr_valid[j]

          if not s.entries_read_data_valid[i]:
            s.invalid_addr_chain[i].v = i
            s.invalid_addr_valid[i].v = 1
          else:
            s.invalid_addr_chain[i].v = s.invalid_addr_chain[j]
            s.invalid_addr_valid[i].v = s.invalid_addr_valid[j]

    s.overwrite = Wire(1)

    @s.combinational
    def compute_overwrite():
      s.overwrite.v = not s.write_remove and not s.write_addr_valid[
          nregs - 1] and not s.invalid_addr_valid[nregs - 1]

    for i in range(nregs):

      @s.combinational
      def handle_write(i=i):
        s.entries[i].write_call.v = s.write_call and (
            (s.overwrite and s.overwrite_counter.read_data == i) or
            (s.write_addr_chain[nregs - 1] == i and
             s.write_addr_valid[nregs - 1]) or
            (not s.write_addr_valid[nregs - 1] and
             s.invalid_addr_chain[nregs - 1] == i and
             s.invalid_addr_valid[nregs - 1] and not s.write_remove))
        s.entries_write_data_key[i].v = s.write_key
        s.entries_write_data_value[i].v = s.write_value
        s.entries_write_data_valid[i].v = not s.write_remove

    @s.combinational
    def update_overwrite_counter(nregsm1=nregs - 1):
      if s.write_call and s.overwrite:
        s.overwrite_counter.write_call.v = 1
        if s.overwrite_counter.read_data == nregsm1:
          s.overwrite_counter.write_data.v = 0
        else:
          s.overwrite_counter.write_data.v = s.overwrite_counter.read_data + 1
      else:
        s.overwrite_counter.write_call.v = 0
        s.overwrite_counter.write_data.v = 0
