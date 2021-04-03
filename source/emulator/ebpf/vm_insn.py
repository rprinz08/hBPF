import sys
import os
import struct
from colorama import Fore, Back, Style
from emulator.ebpf.constants import *
from emulator.ebpf.tools import *


class Instruction():

    def __init__(self, word, swap_endian=True):

        if not isinstance(word, int):
                raise Exception("Invalid opcode ({})".format(word))
        if word > 0xffffffffffffffff or word < -1:
                raise Exception("Invalid opcode (0x{:016x})".format(word))

        self._swap_endian = swap_endian
        self._word = word

        # Represents a eBPF instruction.
        # See https://www.kernel.org/doc/Documentation/networking/filter.txt
        # for more information.

        # Layout of an eBPF instruction. VM internaly only works with
        # little-endian byte-order.

        # MSB                                                        LSB
        # +------------------------+----------------+----+----+--------+
        # |immediate               |offset          |src |dst |opcode  |
        # +------------------------+----------------+----+----+--------+
        # 63                     32               16   12    8        0

        #Inst = struct.Struct("BBHI")
        #code, regs, off, imm = Inst.unpack_from(data, offset)
        #dst_reg = regs & 0xf
        #src_reg = (regs >> 4) & 0xf
        #cls = code & 7

        self._opc = word & 0xff                # 0x00000000000000ff
        self._dst = (word >> 8) & 0x0f         # 0x0000000000000f00
        self._src = (word >> 12) & 0x0f        # 0x000000000000f000
        self._off = (word >> 16) & 0xffff      # 0x00000000ffff0000
        self._imm = (word >> 32) & 0xffffffff  # 0xffffffff00000000

        self._off_s = int16(self._off)
        self._imm_s = int32(self._imm)

        self._cls = self._opc & 0b111


    @property
    def word(self):
        return self._word

    @property
    def op_code(self):
        return self._opc

    @property
    def op_class(self):
        return self._cls

    @property
    def destination(self):
        return self._dst
    @property
    def dst(self):
        return self._dst

    @property
    def source(self):
        return self._src
    @property
    def src(self):
        return self._src

    @property
    def offset(self):
        return self._off
    @property
    def off(self):
        return self._off
    @property
    def offset_s(self):
        return self._off_s
    @property
    def off_s(self):
        return self._off_s

    @property
    def immediate(self):
        return self._imm
    @property
    def imm(self):
        return self._imm
    @property
    def immediate_s(self):
        return self._imm_s
    @property
    def imm_s(self):
        return self._imm_s


    def print(self):
        print("{}OpCode: {}0x{:02x}{}, Dst: {}0x{:1x}{}, Src: {}0x{:1x}{}, "
            "Offset: {}0x{:04x}{}, Imm: {}0x{:08x}{}".format(
                IND,
                Fore.CYAN, self.op_code, Fore.RESET,
                Fore.CYAN, self.destination, Fore.RESET,
                Fore.CYAN, self.source, Fore.RESET,
                Fore.CYAN, self.offset, Fore.RESET,
                Fore.CYAN, self.immediate, Fore.RESET))
