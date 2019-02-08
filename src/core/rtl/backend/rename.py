from pymtl import *
from util.rtl.interface import Interface, IncludeSome, UseInterface
from util.rtl.method import MethodSpec
from util.rtl.types import Array, canonicalize_type
from core.rtl.controlflow import ControlFlowManagerInterface
from bitutil import clog2, clog2nz
from pclib.rtl import RegEn, RegEnRst, RegRst
from core.rtl.messages import FetchMsg, DecodeMsg, PipelineMsg
from msg.codes import RVInstMask, Opcode, ExceptionCode


class RenameInterface(Interface):

  def __init__(s):
    super(DecodeInterface, s).__init__(
        [
        ],
        ordering_chains=[
            [],
        ],
    )


class Rename(Model):

  def __init__(s, xlen, ilen, areg_tag_nbits):
    UseInterface(s, RenameInterface())
