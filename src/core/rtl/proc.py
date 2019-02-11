from pymtl import *
from util.rtl.interface import Interface, UseInterface
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.frontend.decode import Decode, DecodeInterface
from core.rtl.backend.rename import Rename
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from core.rtl.proc_debug_bus import ProcDebugBusInterface
from mem.rtl.memory_bus import MemoryBusInterface
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface
from mem.rtl.memory_bus import MemMsg, MemMsgType
from config.general import *


class ProcInterface(Interface):

  def __init__(s):
    super(ProcInterface, s).__init__([])


class Proc(Model):
  """
         FRONTEND          :                      BACKEND
                           :                             |          |-> |   CSR   | -> |           |
  |       |    |        |  :  |        |    |       |    |          |-> |  BRANCH | -> |           |    |        |
  | Fetch | -> | Decode | -:> | Rename | -> | Issue | -> | Dispatch |-> |   ALU   | -> | Writeback | -> | Commit |
  |_______|    |________|  :  |________|    |_______|    |__________|-> | MUL/DIV | -> |___________|    |________|
                           :

  1. Fetch: Fetch the instruction word
  2. Decode: Determine control signals
  3. Rename: Rename any aregs, and allocate a seq number
  4. Issue: Issue instructions out of order and operands become ready
  5. Dispatch: Read pregs from RF (or maybe get from bypass network)
  6. Execute: Obvious
  7. Writeback: Write the result into the pref
  8. Commit: Reorder the instruction in a ROB and retire then when they reach the head
  """

  def __init__(s, interface=ProcInterface()):
    UseInterface(s, interface)

    # External ports
    s.memory_bus_interface = MemoryBusInterface(1, 1, 2, 64, 8)
    s.debug_bus_interface = ProcDebugBusInterface(XLEN)

    s.memory_bus_interface.require(s, 'mb', 'recv', -1)
    s.memory_bus_interface.require(s, 'mb', 'send', -1)
    s.debug_bus_interface.require(s, 'db', 'recv')
    s.debug_bus_interface.require(s, 'db', 'send')

    # Control flow
    s.cflow_interface = ControlFlowManagerInterface(XLEN, INST_IDX_NBITS)
    s.cflow = ControlFlowManager(s.cflow_interface, RESET_VECTOR)

    # Dataflow
    s.dflow_interface = DataFlowManagerInterface(XLEN, AREG_COUNT, PREG_COUNT,
                                                 MAX_SPEC_DEPTH, 2, 1)
    s.dflow = DataFlowManager(s.dflow_interface)

    # Mem
    s.mem_controller_interface = BasicMemoryControllerInterface(
        s.memory_bus_interface, ['fetch'])
    s.mem_controller = BasicMemoryController(s.mem_controller_interface)
    s.connect_m(s.mb_recv, s.mem_controller.bus_recv)
    s.connect_m(s.mb_send, s.mem_controller.bus_send)

    # Fetch
    s.fetch_interface = FetchInterface(XLEN, ILEN)
    s.fetch = Fetch(
        s.fetch_interface, s.cflow_interface,
        s.mem_controller_interface.export({
            'fetch_recv': 'recv',
            'fetch_send': 'send'
        }))
    s.connect_m(s.mem_controller.fetch_recv, s.fetch.mem_recv)
    s.connect_m(s.mem_controller.fetch_send, s.fetch.mem_send)
    s.connect_m(s.cflow.check_redirect, s.fetch.check_redirect)

    # Decode
    s.decode_interface = DecodeInterface(XLEN, ILEN, DECODED_IMM_LEN)
    s.decode = Decode(s.decode_interface, s.fetch_interface, s.cflow_interface)
    s.connect_m(s.fetch.get, s.decode.fetch_get)
    s.connect_m(s.cflow.check_redirect, s.decode.cflow_check_redirect)
