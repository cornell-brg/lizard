#=========================================================================
# Decode FL Model
#=========================================================================

from pymtl import *
from msg import MemMsg4B
from msg.fetch import FetchPacket
from msg.decode import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.fl import InValRdyQueueAdapterFL, OutValRdyQueueAdapterFL
from config.general import XLEN, ILEN, ILEN_BYTES, RESET_VECTOR


class DispatchFL(Model):
    def __init__(s):
        # input
        s.instr = InValRdyBundle(FetchPacket())
        s.instr_q = InValRdyQueueAdapterFL(s.instr)

        s.pc = Wire(Bits(XLEN))
        s.decode_q = OutValRdyQueueAdapterFL(DecodePacket())

        @s.tick_fl
        def tick():
            inst = s.instr_q.popleft()
            # Decode it and create packet
            res = DecodePacket()
            if (inst[RVInstMask.OPCODE] == Opcode.OP_IMM): # Reg imm
                res.rs1 = inst[RVInstMask.RS1]
                res.rd = inst[RVInstMask.RD]
                res.imm = inst[RVInstMask.I_IMM]
                if (inst[RVInstMask.FUNCT3] == 0b000): res.inst = RV64Inst.ADDI
                elif (inst[RVInstMask.FUNCT3] == 0b010): res.inst = RV64Inst.SLTI
                elif (inst[RVInstMask.FUNCT3] == 0b011): res.inst = RV64Inst.SLTIU
                elif (inst[RVInstMask.FUNCT3] == 0b100): res.inst = RV64Inst.XORI
                elif (inst[RVInstMask.FUNCT3] == 0b110): res.inst = RV64Inst.ORI
                elif (inst[RVInstMask.FUNCT3] == 0b111): res.inst = RV64Inst.ANDI

            elif (inst[RVInstMask.OPCODE] = Opcode.OP): # reg reg
                res.rs1 = inst[RVInstMask.RS1]
                res.rs2 = inst[RVInstMask.RS2]
                res.rd = inst[RVInstMask.RD]
                if (inst[RVInstMask.FUNCT3] == 0b000):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.ADD
                    elif (inst[RVInstMask.FUNCT7] == 0b0100000): res.inst = RV64Inst.SUB
                elif (inst[RVInstMask.FUNCT3] == 0b001):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.SLL
                elif (inst[RVInstMask.FUNCT3] == 0b010):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.SLT
                elif (inst[RVInstMask.FUNCT3] == 0b011):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.SLTU
                elif (inst[RVInstMask.FUNCT3] == 0b100):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.XOR
                elif (inst[RVInstMask.FUNCT3] == 0b101):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.SRL
                    elif (inst[RVInstMask.FUNCT7] == 0b0100000): res.inst = RV64Inst.SRA
                elif (inst[RVInstMask.FUNCT3] == 0b110):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.OR
                elif (inst[RVInstMask.FUNCT3] == 0b111):
                    if (inst[RVInstMask.FUNCT7] == 0b0000000): res.inst = RV64Inst.AND









    def line_trace(s):
        return str(s.pc)
