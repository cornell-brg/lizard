from pymtl import *

from model.hardware_model import HardwareModel
from model.flmodel import FLModel
from core.rtl.frontend.imm_decoder import ImmDecoderInterface, ImmType
from util.arch import rv64g
from config.general import ILEN


class ImmDecoderFL(FLModel):
  field_map = {
      int(ImmType.IMM_TYPE_I): "i_imm",
      int(ImmType.IMM_TYPE_S): "s_imm",
      int(ImmType.IMM_TYPE_B): "b_imm",
      int(ImmType.IMM_TYPE_U): "u_imm",
      int(ImmType.IMM_TYPE_J): "j_imm",
      int(ImmType.IMM_TYPE_C): "c_imm",
  }

  @HardwareModel.validate
  def __init__(s, interface):
    super(ImmDecoderFL, s).__init__(interface)

    @s.model_method
    def decode(inst, type_):
      inst = Bits(ILEN, inst)
      diss = rv64g.fields[s.field_map[type_]].disassemble(inst)

      extension = sext
      if type_ == ImmType.IMM_TYPE_C:
        extension = zext

      return extension(diss, s.interface.decoded_length)
