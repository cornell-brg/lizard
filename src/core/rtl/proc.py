from pymtl import *
from core.rtl.controlflow import ControlFlowManager, ControlFlowManagerInterface
from core.rtl.frontend.fetch import Fetch
from core.rtl.frontend.decode import Decode
from core.rtl.backend.rename import Rename
from core.rtl.dataflow import DataFlowManager

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
    s.cflow_ = ControlFlowManager(XLEN, RESET_VECTOR, INST_IDX_NBITS)
    s.dflow_ = DataFlowManager(XLEN, AREG_COUNT, PREG_COUNT, MAX_SPEC_DEPTH, 2,
                               1)

    s.fetch_ = Fetch(XLEN, ILEN, INST_IDX_NBITS)
    s.decode_ = Decode(XLEN, ILEN, AREG_IDX_NBITS)
    s.rename_ = Rename(XLEN, INST_IDX_NBITS, AREG_COUNT, AREG_IDX_NBITS,
                       PREG_COUNT, MAX_SPEC_DEPTH, 2, 1)
