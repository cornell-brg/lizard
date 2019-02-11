from pymtl import *
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.frontend.fetch import Fetch, FetchInterface
from core.rtl.frontend.decode import Decode, DecodeInterface
from core.rtl.backend.rename import Rename
from core.rtl.dataflow import DataFlowManager, DataFlowManagerInterface
from mem.rtl.basic_memory_controller import BasicMemoryController, BasicMemoryControllerInterface
from mem.rtl.memory_bus import MemMsg, MemMsgType
from config.general import *


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

  def __init__(s):
    # Control Flow
    s.cflow_interface = ControlFlowManagerInterface(XLEN, INST_IDX_NBITS)
    s.cflow = ControlFlowManager(s.cflow_interface, RESET_VECTOR)

    # Dataflow
    s.dflow_interface = DataFlowManagerInterface(XLEN, AREG_COUNT, PREG_COUNT,
                                                 MAX_SPEC_DEPTH, 2, 1)
    s.dflow = DataFlowManager(s.dflow_interface)

    # Mem
    s.mem_msg = MemMsg(1, 2, 64, 8)
    s.mem_controller_interface = BasicMemoryControllerInterface(
        s.mem_msg, ['fetch'])

    # Fetch
    s.fetch_interface = FetchInterface(XLEN, ILEN)
    s.fetch = Fetch(
        s.fetch_interface, s.cflow_interface,
        s.mem_controller_interface.export({
            'fetch_recv': 'recv',
            'fetch_send': 'send'
        }), s.mem_msg)

    # Decode
    s.decode_interface = DecodeInterface(XLEN, ILEN, DECODED_IMM_LEN)
    s.decode = Decode(s.decode_interface, s.fetch_interface, s.cflow_interface)
