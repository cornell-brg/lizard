from pymtl import *
from lizard.bitutil import clog2, clog2nz
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type
from lizard.util.sync_ram import SynchronousRAMInterface, SynchronousRAM


class BranchPredictorInterface(Interface):

  def __init__(s, pc_nbits, hist_idx_nbits, hist_nbits,
    pht_nbits, hasher='concat'):
    assert hasher in ['concat', 'xor']

    s.pc_nbits = pc_nbits
    s.hist_idx_nbits = hist_idx_nbits
    s.hist_nbits = hist_nbits
    s.pht_nbits = pht_nbits
    s.hasher = hasher

    s.pred_idx = max(s.hist_idx_nbits + s.pht_nbits, 1)

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
                'idx': s.pred_idx,
                'taken': Bits(1),
            },
            call=True,
            rdy=False,
        ),
    ],)


class GlobalBranchPredictor(Model):

  def __init__(s, interface):
    UseInterface(s, interface)
    pht_nbits = s.interface.pht_nbits
    hist_nbits = s.interface.hist_nbits
    hist_idx_nbits = s.interface.hist_idx_nbits
    hasher = s.interface.hasher
    pred_idx = s.interface.pred_idx

    if hasher == 'concat':
      pc_hash_nbits = pht_nbits - hist_nbits
    else:
      pc_hash_nbits = pht_nbits

    # This stores the global history
    hist_iface = SynchronousRAMInterface(hist_nbits, 2**hist_idx_nbits, 2, 1,
                                         False)
    s.bhsrt = SynchronousRAM(hist_iface)

    pht_iface = SynchronousRAMInterface(2, 2**pht_nbits, 2, 1, False)
    s.pht = SynchronousRAM(hist_iface)

    # Store the PC on a prediction
    s.reg_pc_predict = Register(
        RegisterInterface(Bits(s.interface.pc_nbits), enable=True))
    s.connect(s.reg_pc_predict.write_call, s.predict_call)
    s.connect(s.reg_pc_predict.write_data, s.predict_pc)
    # We need to track what predictions are valid
    s.reg_active0 = Register(RegisterInterface(Bits(1), enable=False))
    s.connect(s.reg_active0.write_data, s.predict_call)
    s.reg_active1 = Register(RegisterInterface(Bits(1), enable=False))
    s.connect(s.reg_active1.write_data, s.reg_active0.read_data)

    s.pht_idx = Wire(pht_nbits)
    s.pht_pc_idx = Wire(pht_nbits)
    s.pht_hist_idx = Wire(pht_nbits)

    s.connect(s.pht.read_next, s.pht_idx)

    # Read the stored pc
    if pc_hash_nbits > 0:
      @s.combinational
      def zext_pht_pc():
        s.pht_pc_idx.v = s.reg_pc_predict.read_data[0:pc_hash_nbits]
    else:
      s.connect_wire(s.pht_pc_idx, 0)

    # Connect the pc to the index bits of the BHSRT
    if hist_idx_nbits > 0:
      @s.combinational
      def pc_index():
        s.bhsrt.read_next_addr[0].v = s.predict_pc[0:hist_idx_nbits]
    else:
      s.connect_wire(s.bhsrt.read_next[0], 0)

    # Figure out the PC bits for indexing into pht
    if hist_nbits > 0:
      @s.combinational
      def zext_pht_hist():
        s.pht_pc_idx.v = s.bhsrt.read_addr_next[0][0:hist_nbits]
    else:
      s.connect_wire(s.pht_pc_idx, 0)

    # Combine the pattern histroy with the pc:
    if hasher == 'concat':
      @s.combinational
      def pc_idx():
        s.pht_idx.v = (s.pht_pc_idx << hist_nbits) | s.pht_hist_idx
    else:

      @s.combinational
      def pc_idx():
        s.pht_idx.v = s.pht_pc_idx ^ s.pht_hist_idx

    # Set the prediction
    @s.combinational
    def output_prediction():
      s.prediction_rdv.v = s.reg_active1.read_data
      # We predict taken if the sat counter is 2 or 3
      s.prediction_taken.v = s.pht.read_data[0] > 1

    # Handle the update
    s.reg_update0 = Register(RegisterInterface(Bits(1), enable=False))
    s.update_bhsrt_idx = Register(RegisterInterface(Bits(max(1, hist_idx_nbits)), enable=True))
    s.update_pht_idx = Register(RegisterInterface(Bits(max(1, pht_nbits)), enable=True))
    s.update_taken = Register(RegisterInterface(Bits(1), enable=True))
    s.connect(s.reg_update0.write_data, s.update_call)
    s.connect(s.update_bhsrt_idx.write_call, s.update_call)
    s.connect(s.update_pht_idx.write_call, s.update_call)
    s.connect(s.update_taken.write_call, s.update_call)
    s.connect(s.update_taken.write_data, s.update_taken)

    # We call write the next cycle
    s.connect(s.bhsrt.write_call[0], s.reg_update0.read_data)
    s.connect(s.bhsrt.write_addr[0], s.update_bhsrt_idx.read_data)
    s.connect(s.pht.write_call[0], s.reg_update0.read_data)
    s.connect(s.pht.write_addr[0], s.update_pht_idx.read_data)

    # Read the BHSRT
    if hist_idx_nbits > 0:
      @s.combinational
      def set_bhsrt_update_idx():
        s.update_bhsrt_idx.write_data.v = s.pred_idx[0:hist_idx_nbits]
    else:
      @s.combinational
      def set_bhsrt_update_idx():
        s.update_bhsrt_idx.write_data.v = 0

    # Read the PHT
    if pht_nbits > 0:
      @s.combinational
      def set_bhsrt_update_idx():
        s.update_pht_idx.write_data.v = s.pred_idx[hist_idx_nbits:pred_idx]
    else:
      @s.combinational
      def set_bhsrt_update_idx():
        s.update_pht_idx.write_data.v = 0

    # Set the read addrs
    @s.combinational
    def set_update_addrs():
      s.bhsrt.read_next_addr[1].v = s.update_bhsrt_idx.write_data
      s.pht.read_next_addr[1].v = s.update_pht_idx.write_data

    if hist_nbits > 0:
      @s.combinational
      def set_update_hist_writeback():
        s.bhsrt.write_data[0].v = (s.bhsrt.read_data[1] << 1) + s.update_taken.read_data

    @s.combinational
    def update_sat_counter():
      s.pht.write_data[0].v = s.pht.read_data[1]
      if s.pht.read_data[1] < 3 and s.update_taken.read_data:
        s.pht.write_data[0].v = s.pht.read_data[1] + 1
      elif s.pht.read_data[1] > 0 and not s.update_taken.read_data:
        s.pht.write_data[0].v = s.pht.read_data[1] - 1

  def line_trace(s):
    return ":".join(["{}".format(x) for x in s.regs])
