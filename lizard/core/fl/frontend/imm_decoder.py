from pymtl import *

from lizard.model.hardware_model import HardwareModel
from lizard.model.flmodel import FLModel
from lizard.core.rtl.frontend.imm_decoder import ImmType
from lizard.util.arch import rv64g
from lizard.config.general import ILEN


class ImmDecoderFL(FLModel):
  field_map = {
      int(ImmType.IMM_TYPE_I): "i_imm",
      int(ImmType.IMM_TYPE_S): "s_imm",
      int(ImmType.IMM_TYPE_B): "b_imm",
      int(ImmType.IMM_TYPE_U): "u_imm",
      int(ImmType.IMM_TYPE_J): "j_imm",
      int(ImmType.IMM_TYPE_C): "c_imm",
      int(ImmType.IMM_TYPE_SHAMT32): "shamt32",
      int(ImmType.IMM_TYPE_SHAMT64): "shamt64",
  }

  @HardwareModel.validate
  def __init__(s, interface):
    super(ImmDecoderFL, s).__init__(interface)

    @s.model_method
    def decode(inst, type_):
      inst = Bits(ILEN, inst)
      diss = rv64g.fields[s.field_map[type_]].disassemble(inst)

      extension = sext
      if type_ == ImmType.IMM_TYPE_C or type_ == ImmType.IMM_TYPE_SHAMT32 or type_ == ImmType.IMM_TYPE_SHAMT64:
        extension = zext

      return extension(diss, s.interface.decoded_length)
