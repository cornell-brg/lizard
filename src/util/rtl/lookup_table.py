from pymtl import *
from util.rtl.interface import Interface, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import canonicalize_type


class LookupTableInterface(Interface):

  def __init__(s, in_type, out_type):
    s.In = canonicalize_type(in_type)
    s.Out = canonicalize_type(out_type)

    super(LookupTableInterface, s).__init__([
        MethodSpec(
            'lookup',
            args={
                'in_': s.In,
            },
            rets={
                'out': s.Out,
                'valid': Bits(1),
            },
            call=False,
            rdy=False,
        ),
    ])


class LookupTable(Model):

  def __init__(s, interface, mapping):
    UseInterface(s, interface)

    size = len(mapping)
    s.out_chain = [Wire(s.interface.Out) for _ in range(size + 1)]
    s.valid_chain = [Wire(1) for _ in range(size + 1)]
    s.connect(s.out_chain[0], 0)
    s.connect(s.valid_chain[0], 0)

    for i, (target, output) in enumerate(mapping.iteritems()):

      @s.combinational
      def chain(curr=i + 1, last=i, target=int(target), output=int(output)):
        if s.lookup_in_ == target:
          s.out_chain[curr].v = output
          s.valid_chain[curr].v = 1
        else:
          s.out_chain[curr].v = s.out_chain[last]
          s.valid_chain[curr].v = s.valid_chain[last]

    s.connect(s.lookup_out, s.out_chain[-1])
    s.connect(s.lookup_valid, s.valid_chain[-1])

  def line_trace(s):
    return "{} ->({}) {}".format(s.lookup_in_, s.lookup_valid, s.lookup_out)
