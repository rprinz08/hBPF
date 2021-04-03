import sys
import os
import struct
from pprint import pprint

from emulator.ebpf.constants import *
from emulator.ebpf.tools import *


class STORE():

    def __init__(self, vm):
        self.vm = vm

        # Decoder for store OpCodes.
        self._decoder = {
            LDST_IMM   : self._imm,
            LDST_ABS   : self._abs,
            LDST_IND   : self._ind,
            LDST_MEM   : self._mem,
            LDST_XADD  : self._xadd
        }


    def decode(self, insn):
        op_len = (insn.op_code >> 3) & 0b11
        op_mod = (insn.op_code >> 5) & 0b111

        self._decoder.get(op_mod, self._error)(op_mod, op_len, insn)
        return self.vm.ip + 1


    # TODO: Store handlers.
    @disassemble("ST", "imm")
    def _imm(self, op_mod, op_len, insn):
        self._error(op_mod, op_len, insn)

    @disassemble("ST", "abs")
    def _abs(self, op_mod, op_len, insn):
        self._error(op_mod, op_len, insn)


    @disassemble("ST", "ind")
    def _ind(self, op_mod, op_len, insn):
        self._error(op_mod, op_len, insn)


    @disassemble("ST", "stx")
    def _mem(self, op_mod, op_len, insn):
        if insn.op_class == OPC_ST:
            mi = self.vm.regs[insn.destination] + insn.offset
            if op_len == LEN_B:
                self.vm.data_mem[mi] = insn.immediate
            elif op_len == LEN_H:
                self.vm.data_mem[mi:mi+2] = int.to_bytes(insn.immediate, 2,
                                                byteorder="little", signed=False)
            elif op_len == LEN_W:
                self.vm.data_mem[mi:mi+4] = int.to_bytes(insn.immediate, 4,
                                                byteorder="little", signed=False)
            elif op_len == LEN_DW:
                self.vm.data_mem[mi:mi+8] = int.to_bytes(insn.immediate, 8,
                                                byteorder="little", signed=False)
        elif insn.op_class == OPC_STX:
            mi = self.vm.regs[insn.destination] + insn.offset
            if op_len == LEN_B:
                self.vm.data_mem[mi] = self.vm.regs[insn.source]
            elif op_len == LEN_H:
                self.vm.data_mem[mi:mi+2] = int.to_bytes(self.vm.regs[insn.source], 2,
                                                byteorder="little", signed=False)
            elif op_len == LEN_W:
                self.vm.data_mem[mi:mi+4] = int.to_bytes(self.vm.regs[insn.source], 4,
                                                byteorder="little", signed=False)
            elif op_len == LEN_DW:
                self.vm.data_mem[mi:mi+8] = int.to_bytes(self.vm.regs[insn.source], 8,
                                                byteorder="little", signed=False)


    @disassemble("ST", "xadd")
    def _xadd(self, op_mod, op_len, insn):
        self._error(op_mod, op_len, insn)


    def _error(self, op_mod, op_len, insn, *args):
        raise Exception("Invalid STORE instruction: 0x{:016x}".format(insn.word))
