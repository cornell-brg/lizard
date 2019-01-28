from msg.data import *
from msg.codes import *

from util.rtl.interface import Interface, IncludeSome
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from util.rtl.freelist import FreeList
from util.rtl.registerfile import RegisterFile
from core.rtl.renametable import RenameTableInterface, RenameTable

from pclib.ifcs import InValRdyBundle, OutValRdyBundle


class PregState(BitStructDefinition):

  def __init__(s):
    s.value = BitField(XLEN)
    s.ready = BitField(1)


class DataFlowManagerInterface(Interface):

  def __init__(s, naregs, npregs, nsnapshots, num_src_ports, num_dst_ports):
    rename_table_interface = RenameTableInterface(naregs, npregs, 0, 0,
                                                  nsnapshots)

    s.Areg = s.rename_table_interface.Areg
    s.Preg = s.rename_table_interface.Preg
    s.SnapshotId = s.rename_table_interface.SnapshotId

    super(DataFlowManagerInterface, s).__init__(
        [
            MethodSpec(
                'get_src',
                args={
                    'areg': s.Areg,
                },
                rets={
                    'preg': s.Preg,
                },
                call=False,
                rdy=False,
                count=num_src_ports,
            ),
            MethodSpec(
                'get_dst',
                args={
                    'areg': s.Areg,
                },
                rets={
                    'success': Bits(1),
                    'tag': s.Preg,
                },
                call=True,
                rdy=False,
                count=num_dst_ports,
            ),
            MethodSpec(
                'read_tag',
                args={
                    'tag': s.Preg,
                },
                rets={
                    'ready': Bits(1),
                    'value': Bits(XLEN),
                },
                call=False,
                rdy=False,
                count=num_src_ports,
            ),
            MethodSpec(
                'write_tag',
                args={
                    'tag': s.Preg,
                    'value': Bits(XLEN),
                },
                rets=None,
                call=True,
                rdy=False,
                count=num_dst_ports,
            ),
            MethodSpec(
                'commit_tag',
                args={
                    'tag': s.Preg,
                },
                rets=None,
                call=True,
                rdy=False,
                count=num_dst_ports,
            ),
            MethodSpec(
                'rollback',
                args=None,
                rets=None,
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'read_csr',
                args={
                    'csr_num': Bits(CSR_SPEC_NBITS),
                },
                rets={
                    'result': Bits(XLEN),
                    'success': Bits(1),
                },
                call=True,
                rets=False,
            ),
            MethodSpec(
                'write_csr',
                args={
                    'csr_num': Bits(CSR_SPEC_NBITS),
                    'value': Bits(XLEN),
                },
                rets={
                    'success': Bits(1),
                },
                call=True,
                rdy=False,
            ),
            MethodSpec(
                'snapshot',
                args=None,
                rets={
                    'id': s.SnapshotId,
                },
                call=True,
                rdy=True,
            ),
            MethodSpec(
                'free_snapshot',
                args={
                    'id': s.SnapshotId,
                },
                rets=None,
                call=True,
                rdy=False,
            ),
        ],
        bases=[
            IncludeSome(rename_table_interface, {'restore'}),
        ],
        ordering_chains=[
            [
                'commit_tag', 'write_tag', 'get_src', 'get_dst', 'read_tag',
                'snapshot', 'free_snapshot', 'restore', 'rollback'
            ],
        ],
    )


class DataFlowManager(Model):

  def __init__(s, num_src_ports, num_dst_ports):
    s.interface = DataFlowManagerInterface(
        naregs=AREG_COUNT, npregs=PREG_COUNT, nsnapshots=MAX_SPEC_DEPTH)

    s.mngr2proc = InValRdyBundle(Bits(XLEN))
    s.proc2mngr = OutValRdyBundle(Bits(XLEN))

    # Reserve the highest tag for x0
    # Free list with 2 alloc ports, 1 free port, and AREG_COUNT - 1 used slots
    # initially
    s.free_regs = FreeList(
        PREG_COUNT - 1,
        num_src_ports,
        num_dst_ports,
        False,
        False,
        used_slots_initial=AREG_COUNT - 1)
    # arf_used_pregs tracks the physical registers used by the current architectural state
    # arf_used_pregs[i] is 1 if preg i is used by the arf, and 0 otherwise
    # on reset, the ARF is backed by pregs [0, AREG_COUNT - 1]
    arf_used_pregs_reset = [Bits(1, 0) for _ in range(PREG_COUNT - 1)]

    for i in range(AREG_COUNT):
      arf_used_pregs_reset[i] = Bits(1, 1)

    s.arf_used_pregs = RegisterFile(
        Bits(1),
        PREG_COUNT - 1,
        0,  # no read ports needed, only a dump port
        num_dst_ports,  # have to write for every instruction that commits
        False,  # no read ports, so we don't need a write-read bypass
        dump_port=True,  # only used for reading
        reset_values=arf_used_pregs_reset)

    # Build the initial rename table.
    # x0 -> don't care
    # xn -> n-1
    initial_map = [0] + [x for x in range(AREG_COUNT - 1)]
    s.rename_table = RenameTable(AREG_COUNT, PREG_COUNT, num_src_ports,
                                 num_dst_ports, MAX_SPEC_DEPTH, True,
                                 initial_map)

    preg_reset = [PregState() for _ in range(PREG_COUNT)]
    inverse_reset = [Bits(PREG_IDX_NBITS) for _ in range(PREG_COUNT)]

    # Only non x0 registers have an initial state
    for x in range(AREG_COUNT - 1):
      preg_reset[x].value = 0
      preg_reset[x].ready = 1
      # Initially p0 is x1
      inverse_reset[x] = x + 1
    s.preg_file = RegisterFile(
        PregState(),
        PREG_COUNT,
        num_src_ports,
        num_dst_ports * 2,
        True,
        reset_values=preg_reset)
    s.inverse = RegisterFile(
        Bits(AREG_IDX_NBITS),
        PREG_COUNT,
        num_dst_ports,
        num_dst_ports,
        True,
        reset_values=inverse_reset)

    s.areg_file = RegisterFile(
        Bits(PREG_IDX_NBITS),
        AREG_COUNT,
        num_dst_ports,
        num_dst_ports,
        False,
        dump_port=True,
        reset_values=initial_map)

    s.snapshot_port = s.interface.snapshot.in_port()
    s.connect(s.snapshot_port, s.rename_table.snapshot_port)

    s.restore_port = s.interface.restore.in_port()
    s.connect(s.restore_port, s.rename_table.restore_port)

    s.free_snapshot_port = s.interface.free_snapshot.in_port()
    s.connect(s.free_snapshot_port, s.rename_table.free_snapshot_port)

    s.rollback_port = s.interface.rollback.in_port()
    s.connect(s.rollback_port.call, s.rename_table.external_restore_en)
    for i in range(AREG_COUNT):
      s.connect(s.areg_file.dump_out[i], s.rename_table.external_restore_in[i])

    s.get_src_ports = [
        s.interface.get_src.in_port() for _ in range(num_src_ports)
    ]
    for i in range(num_src_ports):
      s.connect(s.rename_table.read_ports[i].areg, s.get_src_ports[i].areg)
      s.connect(s.rename_table.read_ports[i].preg, s.get_src_ports[i].preg)

    s.get_dst_ports = [
        s.interface.get_dst.in_port() for _ in range(num_dst_ports)
    ]
    for i in range(num_dst_ports):
      # only call free list if areg != 0 and it is ready
      @s.combinational
      def handle_dst_alloc(i=i):
        s.free_regs.alloc_ports[i].call.v = s.free_regs.alloc_ports[
            i].rdy and s.get_dst_ports[i].call and s.get_dst_ports[i].areg != 0

      # only write to the rename table if we are calling
      @s.combinational
      def handle_dst_alloc_write(i=i):
        s.rename_table.write_ports[i].call.v = s.free_regs.alloc_ports[i].call

      # addr is areg and data is preg
      s.connect(s.get_dst_ports[i].areg, s.rename_table.write_ports[i].areg)
      s.connect(s.free_regs.alloc_ports[i].index,
                s.rename_table.write_ports[i].preg)

      # result is the either the result from the free list or the zero tag
      # success is if we were able to call the free list or the areg was 0
      @s.combinational
      def handle_dst_result(i=i):
        if s.get_dst_ports[i].areg == 0:
          s.get_dst_ports[i].success.v = 1
          s.get_dst_ports[i].tag.v = s.rename_table.ZERO_TAG
        else:
          s.get_dst_ports[i].success.v = s.free_regs.alloc_ports[i].call
          s.get_dst_ports[i].tag.v = s.free_regs.alloc_ports[i].index

      s.connect(s.preg_file.wr_ports[i].call,
                s.rename_table.write_ports[i].call)
      s.connect(s.preg_file.wr_ports[i].addr, s.free_regs.alloc_ports[i].index)
      s.connect(s.preg_file.wr_ports[i].data.value, 0)
      s.connect(s.preg_file.wr_ports[i].data.ready, 0)

      s.connect(s.inverse.wr_ports[i].call, s.rename_table.write_ports[i].call)
      s.connect(s.inverse.wr_ports[i].addr, s.free_regs.alloc_ports[i].index)
      s.connect(s.inverse.wr_ports[i].data, s.get_dst_ports[i].areg)

    s.read_tag_ports = [
        s.interface.read_tag.in_port() for _ in range(num_src_ports)
    ]
    # PYMTL_BROKEN workaround
    s.workaround_preg_file_rd_ports_data_value = [
        Wire(XLEN) for _ in range(num_src_ports)
    ]
    s.workaround_preg_file_rd_ports_data_ready = [
        Wire(1) for _ in range(num_src_ports)
    ]
    for i in range(num_src_ports):
      s.connect(s.preg_file.rd_ports[i].data.value,
                s.workaround_preg_file_rd_ports_data_value[i])
      s.connect(s.preg_file.rd_ports[i].data.ready,
                s.workaround_preg_file_rd_ports_data_ready[i])

    for i in range(num_src_ports):
      s.connect(s.preg_file.rd_ports[i].addr, s.read_tag_ports[i].tag)

      @s.combinational
      def handle_src_read(i=i):
        if s.read_tag_ports[i].tag == s.rename_table.ZERO_TAG:
          s.read_tag_ports[i].ready.v = 1
          s.read_tag_ports[i].value.v = 0
        else:
          s.read_tag_ports[
              i].ready.v = s.workaround_preg_file_rd_ports_data_ready[i]
          s.read_tag_ports[
              i].value.v = s.workaround_preg_file_rd_ports_data_value[i]

    s.write_tag_ports = [
        s.interface.write_tag.in_port() for _ in range(num_src_ports)
    ]
    for i in range(num_dst_ports):
      # only write if not zero tag
      # note that we write using special ports
      # get_dst also causes writes to the preg_file, so write_tag uses its own ports
      # at higher indicies. There shouldn't be any conflicts however.
      @s.combinational
      def handle_write_call(i=i):
        s.preg_file.wr_ports[i + num_dst_ports].call.v = s.write_tag_ports[
            i].call and s.write_tag_ports[i].tag != s.rename_table.ZERO_TAG

      s.connect(s.preg_file.wr_ports[i + num_dst_ports].addr,
                s.write_tag_ports[i].tag)
      s.connect(s.preg_file.wr_ports[i + num_dst_ports].data.value,
                s.write_tag_ports[i].value)
      # value is ready if we are writing it
      s.connect(s.preg_file.wr_ports[i + num_dst_ports].data.ready,
                s.write_tag_ports[i].call)

    s.free_tag_ports = [
        s.interface.free_tag.in_port() for _ in range(num_dst_ports)
    ]

    for i in range(num_dst_ports):
      # read the inverse
      s.connect(s.inverse.rd_ports[i].addr, s.free_tag_ports[i].tag)
      # get the old physical register
      s.connect(s.areg_file.rd_ports[i].addr, s.inverse.rd_ports[i].data)

      # connect the areg_file write inputs
      s.connect(s.areg_file.wr_ports[i].addr, s.inverse.rd_ports[i].data)
      s.connect(s.areg_file.wr_ports[i].data, s.free_tag_ports[i].tag)

      # only free if not zero tag
      # if committing free old tag, otherwise free input tag
      @s.combinational
      def handle_free_tag_call(i=i):
        if s.free_tag_ports[i].commit:
          s.free_regs.free_ports[i].index.v = s.areg_file.rd_ports[i].data
          s.free_regs.free_ports[i].call.v = s.free_tag_ports[
              i].call and s.inverse.rd_ports[i].data != 0
        else:
          s.free_regs.free_ports[i].index.v = s.free_tag_ports[i].tag
          s.free_regs.free_ports[i].call.v = s.free_tag_ports[
              i].call and s.free_tag_ports[i].tag != s.rename_table.ZERO_TAG

        # write into the areg file if commit
        s.areg_file.wr_ports[
            i].call.v = s.free_tag_ports[i].call and s.free_tag_ports[i].commit

    s.read_csr_port = s.interface.read_csr.in_port()

    @s.combinational
    def handle_read_csr():
      s.read_csr_port.result.v = 0
      s.read_csr_port.success.v = 0

      s.mngr2proc.rdy.v = 0

      if s.read_csr_port.call:
        if s.read_csr_port.csr_num == CsrRegisters.mngr2proc:
          s.read_csr_port.result.v = s.mngr2proc.msg
          s.read_csr_port.success.v = s.mngr2proc.val
          # we are ready if data is valid and we made it here
          s.mngr2proc.rdy.v = s.mngr2proc.val
        else:
          # no other CSRs supported return 0
          s.read_csr_port.result.v = 0
          s.read_csr_port.success.v = 1

    s.write_csr_port = s.interface.write_csr.in_port()

    @s.combinational
    def handle_write_csr():
      s.write_csr_port.success.v = 0
      s.proc2mngr.msg.v = 0
      s.proc2mngr.val.v = 0

      if s.write_csr_port.call:
        if s.write_csr_port.csr_num == CsrRegisters.proc2mngr:
          s.write_csr_port.success.v = s.proc2mngr.rdy
          s.proc2mngr.msg.v = s.write_csr_port.value
          s.proc2mngr.val.v = s.proc2mngr.rdy
        else:
          # no other CSRs supported
          s.write_csr_port.success.v = 1

  def line_trace(s):
    return "<dataflow>"
