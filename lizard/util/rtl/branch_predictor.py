from pymtl import *
from lizard.bitutil import clog2, clog2nz
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type
from lizard.util.sync_ram import SynchronousRAMInterface, SynchronousRAM


class BranchPredictorInterface(Interface):

  def __init__(s, pc_nbits):
    s.pc_nbits = pc_nbits

    super(BranchPredictorInterface, s).__init__([
        MethodSpec(
            'predict',
            args={
                'pc': s.pc_nbits,
            },
            call=True,
            rdy=False,
        ),
        MethodSpec(
            'prediction',
            rets={
                'taken': Bits(1),
            },
            call=False,
            rdy=True,
        ),
        MethodSpec(
            'update',
            args={
                'pc': s.pc_nbits,
                'taken': Bits(1),
            },
            call=True,
            rdy=False,
        ),
    ],)


class GlobalBranchPredictor(Model):

  def __init__(s,
               interface,
               hist_idx_nbits,
               hist_nbits,
               pht_nbits,
               hasher='concat'):
    UseInterface(s, interface)
    assert hasher in ['concat', 'xor']

    if hasher == 'concat':
      pc_hash_nbits = pht_nbits - hist_nbits
    else:
      pc_hash_nbits = pht_nbits

    assert pc_hash_nbits > 0

    # This stores the global history
    hist_iface = SynchronousRAMInterface(hist_nbits, 2**hist_idx_nbits, 2, 1,
                                         False)
    s.history = SynchronousRAM(hist_iface)

    pht_iface = SynchronousRAMInterface(2, 2**pht_nbits, 1, 1, False)
    s.pht = SynchronousRAM(hist_iface)

    s.reg_pc_predict = Register(
        RegisterInterface(Bits(s.interface.pc_nbits), enable=True))
    s.connect(s.reg_pc_predict.write_call, s.predict_call)
    s.connect(s.reg_pc_predict.write_data, s.predict_pc)

    s.pht_idx = Wire(pht_nbits)
    s.pht_pc_idx = Wire(pht_nbits)
    s.pht_hist_idx = Wire(pht_nbits)

    s.connect(s.pht.read_next, s.pht_idx)

    @s.combinational
    def zext_pht_pc():
      if pc_hash_nbits == 0:
        s.pht_pc_idx.v = 0
      else:
        s.pht_pc_idx.v = s.reg_pc_predict.read_data[0:pc_hash_nbits]

    @s.combinational
    def zext_pht_hist():
      if hist_nbits == 0:
        s.pht_pc_idx.v = 0
      else:
        s.pht_pc_idx.v = s.history.read_data[0][0:hist_nbits]

    if hist_idx_nbits > 0:

      @s.combinational
      def pc_index():
        s.history.read_next[0].v = 0
        if s.predict_call:
          s.history.read_next[0].v = s.predict_pc[0:hist_idx_nbits]
    else:
      s.connect(s.history.read_next[0], 0)

    if hasher == 'concat':

      @s.combinational
      def pc_idx():
        s.pht_idx.v = (s.pht_pc_idx << hist_nbits) | s.pht_hist_idx
    else:

      @s.combinational
      def pc_idx():
        s.pht_idx.v = s.pht_pc_idx ^ s.pht_hist_idx

  def line_trace(s):
    return ":".join(["{}".format(x) for x in s.regs])
