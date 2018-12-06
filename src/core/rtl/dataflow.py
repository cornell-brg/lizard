from msg.data import *
from config.general import *
from msg.codes import *
from util.rtl.freelist import FreeList


class PregState( BitStructDefinition ):

  def __init__( s ):
    s.value = BitField( XLEN )
    s.ready = BitField( 1 )
    s.areg = BitField( REG_SPEC_LEN )


class DataFlowManager( Model ):

  def __init__( s ):
    s.Preg = Bits( REG_TAG_LEN )
    s.Areg = Bits( REG_SPEC_LEN )

    s.mngr2proc = InValRdyBundle( Bits( XLEN ) )
    s.proc2mngr = OutValRdyBundle( Bits( XLEN ) )

    s.SnapshotId = s.rename_table.SnapshotId
    s.snapshot_port = InMethodCallPortBundle( None, { 'id': s.SnapshotId} )
    s.restore_port = InMethodCallPortBundle({
        'id': s.SnapshotId
    },
                                            None,
                                            has_call=True,
                                            has_rdy=False )
    s.free_snapshot_port = InMethodCallPortBundle({
        'id': s.SnapshotId
    },
                                                  None,
                                                  has_call=True,
                                                  has_rdy=False )

    s.rollback_port = InMethodCallPortBundle(
        None, None, has_call=True, has_rdy=False )

    s.get_src_ports = [
        InMethodCallPortBundle({
            'areg': s.Areg
        }, { 'preg': s.Preg},
                               has_call=False,
                               has_rdy=False ) for _ in range( 2 )
    ]

    s.get_dst_ports = [
        InMethodCallPortBundle({
            'areg': s.Areg
        }, {
            'success': Bits( 1 ),
            'tag': s.Preg
        },
                               has_call=True,
                               has_rdy=False ) for _ in range( 1 )
    ]

    s.read_tag_ports = [
        InMethodCallPortBundle({
            'tag': s.Preg
        }, {
            'ready': Bits( 1 ),
            'value': Bits( XLEN )
        },
                               has_call=False,
                               has_rdy=False ) for _ in range( 2 )
    ]

    s.write_tag_ports = [
        InMethodCallPortBundle({
            'tag': s.Preg,
            'value': Bits( XLEN )
        },
                               None,
                               has_call=True,
                               has_rdy=False ) for _ in range( 1 )
    ]

    s.free_tag_ports = [
        InMethodCallPortBundle({
            'tag': s.Preg
        },
                               None,
                               has_call=True,
                               has_rdy=False ) for _ in range( 1 )
    ]

    s.commit_tag_ports = [
        InMethodCallPortBundle({
            'tag': s.Preg
        },
                               None,
                               has_call=True,
                               has_rdy=False ) for _ in range( 1 )
    ]

    s.read_csr_port = InMethodCallPortBundle({
        'csr_num': Bits( CSR_SPEC_LEN )
    }, {
        'result': Bits( XLEN ),
        'success': Bits( 1 )
    },
                                             has_call=True,
                                             has_rdy=False )

    s.write_csr_port = InMethodCallPortBundle({
        'csr_num': Bits( CSR_SPEC_LEN ),
        'value': Bits( XLEN )
    },
                                              has_call=True,
                                              has_rdy=False )

    # Reserve the highest tag for x0
    # Free list with 2 alloc ports, 1 free port, and REG_COUNT - 1 used slots
    # initially
    s.free_regs = FreeList( REG_TAG_COUNT - 1, 2, 1, False, REG_COUNT - 1 )
    # Build the initial rename table.
    # x0 -> don't care
    # xn -> n-1
    initial_map = [ 0 ] + [ x for x in range( REG_COUNT - 1 ) ]
    # Rename table with 2 write ports 1 read port and a constant zero
    s.rename_table = RenameTable( REG_COUNT, REG_TAG_COUNT, 2, 1,
                                  MAX_SPEC_DEPTH, True, initial_map )

    preg_reset = [ PregState() for _ in range( REG_TAG_COUNT ) ]
    # Only non x0 registers have an initial state
    for x in range( REG_COUNT - 1 ):
      preg_state.value = 0
      preg_state.ready = 1
      # Initially p0 is x1
      preg_state.areg = x + 1
    s.preg_file = RegisterFile(
        PregState(), REG_TAG_COUNT, 2, 1, True, reset_values=preg_reset )
    s.areg_file = RegisterFile(
        Bits( REG_TAG_LEN ),
        REG_COUNT,
        1,
        1,
        False,
        dump_port=True,
        reset_values=initial_map )

  def line_trace( s ):
    return "<dataflow>"
