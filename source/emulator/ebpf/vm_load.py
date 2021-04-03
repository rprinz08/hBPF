import sys
import os
import struct
from pprint import pprint

from emulator.ebpf.constants import *
from emulator.ebpf.tools import *
from emulator.ebpf.vm_insn import Instruction


class LOAD():

    def __init__(self, vm):
        self.vm = vm

        # Decoder for load OpCodes.
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
        return self.vm.inc_ip()


    # Load handlers.
    @disassemble("LD", "lddw")
    def _imm(self, op_mod, op_len, insn):
        self.vm.ip = self.vm.inc_ip()
        tmp_insn = Instruction(self.vm.get_word(), swap_endian=self.vm.swap_endian)
        if tmp_insn.op_code != 0x00:
            self._error(op_mod, op_len, tmp_insn)
        self.vm.regs[insn.destination] = insn.immediate | (tmp_insn.imm << 32)


    @disassemble("LD", "ldabs")
    def _abs(self, op_mod, op_len, insn):
        mi = insn.immediate
        if op_len == LEN_B:
            self.vm.r0 = self.vm.data_mem[mi]
        elif op_len == LEN_H:
            self.vm.r0 = int.from_bytes(self.vm.data_mem[mi:mi+2],
                                        byteorder="big", signed=False)
        elif op_len == LEN_W:
            self.vm.r0 = int.from_bytes(self.vm.data_mem[mi:mi+4],
                                        byteorder="big", signed=False)
        elif op_len == LEN_DW:
            self.vm.r0 = int.from_bytes(self.vm.data_mem[mi:mi+8],
                                        byteorder="big", signed=False)


    @disassemble("LD", "ind")
    def _ind(self, op_mod, op_len, insn):
        if op_len == LEN_B:
            self.vm.r0 = insn.immediate & 0x00000000000000ff
        elif op_len == LEN_H:
            self.vm.r0 = insn.immediate & 0x000000000000ffff
        elif op_len == LEN_W:
            self.vm.r0 = self.vm.data_mem[self.vm.regs[insn.source] + insn.immediate] & 0x00000000ffffffff
        elif op_len == LEN_DW:
            self.vm.r0 = insn.immediate & 0xffffffffffffffff


    @disassemble("LD", "ldx")
    def _mem(self, op_mod, op_len, insn):
        mi = self.vm.regs[insn.source] + insn.offset
        if op_len == LEN_B:
            self.vm.regs[insn.destination] = self.vm.data_mem[mi]
        elif op_len == LEN_H:
            self.vm.regs[insn.destination] = int.from_bytes(self.vm.data_mem[mi:mi+2],
                                            byteorder="little", signed=False)
        elif op_len == LEN_W:
            self.vm.regs[insn.destination] = int.from_bytes(self.vm.data_mem[mi:mi+4],
                                            byteorder="little", signed=False)
        elif op_len == LEN_DW:
            self.vm.regs[insn.destination] = int.from_bytes(self.vm.data_mem[mi:mi+8],
                                            byteorder="little", signed=False)


    @disassemble("LD", "xadd")
    def _xadd(self, op_mod, op_len, insn):
        pass


    def _error(self, op_mod, op_len, insn, *args):
        raise Exception("Invalid LOAD instruction: 0x{:016x}".format(insn.word))
