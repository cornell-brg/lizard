from pymtl import *
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.async_ram import AsynchronousRAMInterface, AsynchronousRAM
from lizard.util.rtl.lookup_table import LookupTableInterface, LookupTable


class LookupRegisterFileInterface(Interface):

  def __init__(s, Key, Value, num_read_ports, num_write_ports):
    s.Key = Key
    s.Value = Value
    s.num_read_ports = num_read_ports
    s.num_write_ports = num_write_ports

    super(LookupRegisterFileInterface, s).__init__([
        MethodSpec(
            'read',
            args={
                'key': s.Key,
            },
            rets={
                'value': s.Value,
                'valid': Bits(1),
            },
            call=False,
            rdy=False,
            count=num_read_ports,
        ),
        MethodSpec(
            'write',
            args={
                'key': s.Key,
                'value': s.Value,
            },
            rets={
                'valid': Bits(1),
            },
            call=True,
            rdy=False,
            count=num_write_ports,
        ),
    ])


class LookupRegisterFile(Model):

  def __init__(s, interface, key_groups, reset_values=None):
    """
    key_groups is a list of tuples like [(a, b), c]. Each element in the list
    is a key. If an element is a tuple, all elements of the tuple alias each other.
    """
    UseInterface(s, interface)

    size = len(key_groups)
    Key = s.interface.Key
    Value = s.interface.Value
    num_read_ports = s.interface.num_read_ports
    num_write_ports = s.interface.num_write_ports
    mapping = {}
    for i, group in enumerate(key_groups):
      if not isinstance(group, tuple):
        group = (group,)
      for key in group:
        assert key not in mapping
        mapping[key] = i

    s.async_ram = AsynchronousRAM(
        AsynchronousRAMInterface(Value, size, num_read_ports, num_write_ports),
        reset_values=reset_values)

    def make_lut():
      return LookupTable(
          LookupTableInterface(Key, s.async_ram.interface.Addr), mapping)

    s.read_luts = [make_lut() for _ in range(num_read_ports)]
    s.write_luts = [make_lut() for _ in range(num_write_ports)]

    for i in range(num_read_ports):
      s.connect(s.read_luts[i].lookup_in_, s.read_key[i])
      s.connect(s.async_ram.read_addr[i], s.read_luts[i].lookup_out)
      s.connect(s.read_valid[i], s.read_luts[i].lookup_valid)

      @s.combinational
      def handle_invalid_read(i=i):
        if s.read_luts[i].lookup_valid:
          s.read_value[i].v = s.async_ram.read_data[i]
        else:
          s.read_value[i].v = 0

    for i in range(num_write_ports):
      s.connect(s.write_luts[i].lookup_in_, s.write_key[i])
      s.connect(s.async_ram.write_addr[i], s.write_luts[i].lookup_out)
      s.connect(s.async_ram.write_data[i], s.write_value[i])
      s.connect(s.write_valid[i], s.write_luts[i].lookup_valid)

      @s.combinational
      def compute_write_call(i=i):
        s.async_ram.write_call[
            i].v = s.write_luts[i].lookup_valid and s.write_call[i]
