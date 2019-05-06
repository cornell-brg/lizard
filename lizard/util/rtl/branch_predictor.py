from pymtl import *
from lizard.bitutil import clog2, clog2nz
from lizard.util.rtl.interface import Interface, UseInterface
from lizard.util.rtl.method import MethodSpec
from lizard.util.rtl.types import canonicalize_type
from lizard.util.rtl.sync_ram import SynchronousRAMInterface, SynchronousRAM
from lizard.util.rtl.async_ram import AsynchronousRAMInterface, AsynchronousRAM
from lizard.util.rtl.register import Register, RegisterInterface


class BranchPredictorInterface(Interface):

  def __init__(s, pc_nbits, max_inflight=32):
    s.pc_nbits = pc_nbits
    s.pred_idx = clog2(max_inflight)

    super(BranchPredictorInterface, s).__init__([
        MethodSpec(
            'predict',
            args={
                'pc': s.pc_nbits,
                'idx': s.pred_idx,
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

  def __init__(s, interface, hist_idx_nbits, hist_nbits, pht_nbits, hasher='concat'):
    UseInterface(s, interface)
    assert hasher in ['xor', 'concat']

    pred_idx = s.interface.pred_idx


    # Handle the annoying Bits(0)
    hist_nbits_nz = max(1, hist_nbits)
    nbits_bhsrt_idx_nz = max(1, hist_idx_nbits)
    nbits_pht_idx_nz = max(1, pht_nbits)

    if hasher == 'concat':
      pc_hash_nbits = pht_nbits - hist_nbits
    else:
      pc_hash_nbits = pht_nbits

    s.pht_idx = Wire(nbits_pht_idx_nz)
    s.pht_pc_idx = Wire(nbits_pht_idx_nz)
    s.pht_hist_idx = Wire(nbits_pht_idx_nz)

    # This stores the global history
    hist_iface = SynchronousRAMInterface(hist_nbits_nz, 2**hist_idx_nbits, 2, 1,
                                         False)
    s.bhsrt = SynchronousRAM(hist_iface)

    # Store the saturating counter
    pht_iface = SynchronousRAMInterface(2, 2**nbits_pht_idx_nz, 2, 1, False)
    s.pht = SynchronousRAM( pht_iface)

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
    s.connect(s.prediction_rdy, s.reg_active1.read_data)

    s.branch_index_alloc = Register(RegisterInterface(Bits(pred_idx), enable=True), reset_value=0)
    s.connect(s.branch_index_alloc.write_call, s.predict_call)
    s.branch_index0 = Register(RegisterInterface(Bits(pred_idx), enable=True))
    s.connect(s.branch_index0.write_call, s.predict_call)
    s.connect(s.branch_index0.write_data, s.branch_index_alloc.read_data)

    # Return the prediciton index
    s.connect(s.predict_idx, s.branch_index_alloc.read_data)

    # Keep track of the branch index
    idx_bhsrt_iface = AsynchronousRAMInterface(nbits_bhsrt_idx_nz, 2**pred_idx, 1, 1)
    s.idx_to_bhsrt = AsynchronousRAM(idx_bhsrt_iface)
    idx_pht_iface = AsynchronousRAMInterface(nbits_pht_idx_nz, 2**pred_idx, 1, 1)
    s.idx_to_pht = AsynchronousRAM(idx_pht_iface)

    # Set the BHSRT update
    s.connect(s.idx_to_bhsrt.write_call[0], s.predict_call)
    s.connect(s.idx_to_bhsrt.write_addr[0], s.branch_index_alloc.read_data)

    s.connect(s.idx_to_pht.write_call[0], s.reg_active0.read_data)
    s.connect(s.idx_to_pht.write_addr[0], s.branch_index0.read_data)
    s.connect(s.idx_to_pht.write_data[0], s.pht_idx)

    @s.combinational
    def update_branch_idx():
      s.branch_index_alloc.write_data.v = s.branch_index_alloc.read_data + 1

    # Set the pht read index
    s.connect(s.pht.read_next_addr[0], s.pht_idx)

    # Connect the pc to the index bits of the BHSRT
    if hist_idx_nbits > 0:
      @s.combinational
      def pc_index():
        s.bhsrt.read_next_addr[0].v = s.predict_pc[0:hist_idx_nbits]
        s.idx_to_bhsrt.write_data[0].v = s.bhsrt.read_next_addr[0]
    else:
      s.connect_wire(s.bhsrt.read_next[0], 0)
      s.connect_wire(s.idx_to_bhsrt.write_data[0], 0)


    # Read the stored pc
    if pc_hash_nbits > 0:
      @s.combinational
      def zext_pht_pc():
        s.pht_pc_idx.v = 0
        s.pht_pc_idx[0:pc_hash_nbits].v = s.reg_pc_predict.read_data[0:pc_hash_nbits]
    else:
      s.connect_wire(s.pht_pc_idx, 0)


    # Figure out the PC bits for indexing into pht
    if hist_nbits > 0:
      @s.combinational
      def zext_pht_hist():
        s.pht_hist_idx.v = 0
        s.pht_hist_idx[0:hist_nbits].v = s.bhsrt.read_data[0]
    else:
      s.connect_wire(s.pht_hist_idx, 0)

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
      s.prediction_rdy.v = s.reg_active1.read_data
      # We predict taken if the sat counter is 2 or 3
      s.prediction_taken.v = s.pht.read_data[0] > 1


    ############## Handle the branch resolution updates #####################
    s.reg_update0 = Register(RegisterInterface(Bits(1), enable=False))
    s.update_idx_bhsrt = Register(RegisterInterface(Bits(nbits_bhsrt_idx_nz), enable=True))
    s.update_idx_pht = Register(RegisterInterface(Bits(nbits_pht_idx_nz), enable=True))
    s.reg_update_taken = Register(RegisterInterface(Bits(1), enable=True))

    s.connect(s.reg_update0.write_data, s.update_call)
    s.connect(s.reg_update_taken.write_call, s.update_call)
    s.connect(s.update_idx_bhsrt.write_call, s.update_call)
    s.connect(s.update_idx_pht.write_call, s.update_call)

    # Need to store the index for next cycle
    s.connect(s.reg_update_taken.write_data, s.update_taken)
    s.connect(s.update_idx_bhsrt.write_data, s.idx_to_bhsrt.read_data[0])
    s.connect(s.update_idx_pht.write_data, s.idx_to_pht.read_data[0])

    # Connect the update index into reading the sram
    s.connect(s.idx_to_bhsrt.read_addr[0], s.update_idx)
    s.connect(s.idx_to_pht.read_addr[0], s.update_idx)

    # Set the read adders
    s.connect(s.bhsrt.read_next_addr[1], s.idx_to_bhsrt.read_data[0])
    s.connect(s.pht.read_next_addr[1], s.idx_to_pht.read_data[0])

    # We call write the next cycle
    s.connect(s.bhsrt.write_call[0], s.reg_update0.read_data)
    s.connect(s.bhsrt.write_addr[0], s.update_idx_bhsrt.read_data)
    s.connect(s.pht.write_call[0], s.reg_update0.read_data)
    s.connect(s.pht.write_addr[0], s.update_idx_pht.read_data)


    if hist_nbits > 0:
      @s.combinational
      def set_update_hist_writeback():
        s.bhsrt.write_data[0].v = (s.bhsrt.read_data[1] << 1) + s.reg_update_taken.read_data
    else:
      s.connect(s.bhsrt.write_data[0], 0)

    @s.combinational
    def update_sat_counter():
      s.pht.write_data[0].v = s.pht.read_data[1]
      if s.pht.read_data[1] < 3 and s.reg_update_taken.read_data:
        s.pht.write_data[0].v = s.pht.read_data[1] + 1
      elif s.pht.read_data[1] > 0 and not s.reg_update_taken.read_data:
        s.pht.write_data[0].v = s.pht.read_data[1] - 1

  def line_trace(s):
    return ":".join(["{}".format(x) for x in s.regs])
