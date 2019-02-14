import pytest
from pymtl import *
from model.test_model import run_test_state_machine, ArgumentStrategy
from core.rtl.frontend.imm_decoder import ImmDecoder, ImmDecoderInterface, ImmType
from core.fl.frontend.imm_decoder import ImmDecoderFL
from config.general import DECODED_IMM_LEN


def test_state_machine():
  run_test_state_machine(
      ImmDecoder,
      ImmDecoderFL, (ImmDecoderInterface(DECODED_IMM_LEN)),
      translate_model=False,
      argument_strategy={
          'decode':
              ArgumentStrategy(
                  type_=ArgumentStrategy.value_strategy(ImmType.size - 1))
      })
