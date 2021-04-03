import sys
import os
import struct
from pprint import pprint

from emulator.ebpf.constants import *
from emulator.ebpf.tools import *


class ALU():

    def __init__(self, vm):
        self.vm = vm

        # ALU decoder.
        self._decoder = {
            ALU_ADD  : self._add,
            ALU_SUB  : self._sub,
            ALU_MUL  : self._mul,
            ALU_DIV  : self._div,
            ALU_OR   : self._or,
            ALU_AND  : self._and,
            ALU_LSH  : self._lsh,
            ALU_RSH  : self._rsh,
            ALU_NEG  : self._neg,
            ALU_MOD  : self._mod,
            ALU_XOR  : self._xor,
            ALU_MOV  : self._mov,
            ALU_ARSH : self._arsh,
            ALU_ENDC : self._endc
        }


    def decode(self, insn):
        op_src = (insn.op_code >> 3) & 0b1
        op_opr = (insn.op_code >> 4) & 0b1111

        self._decoder.get(op_opr, self._error)(op_opr, op_src, insn)
        return self.vm.inc_ip()


    # ALU operation handlers.
    @disassemble("ALU", "add")
    def _add(self, op_opr, op_src, insn):
        if insn.op_class == OPC_ALU64:
            if op_src == 0:
                # 0x07  add dst, imm    dst += imm
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] + insn.immediate
            else:
                # 0x0f  add dst, src    dst += src
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] + self.vm.regs[insn.source]

            self.vm.regs[insn.destination] &= MAX_UINT64
        else:
            if op_src == 0:
                # 0x07  add dst, imm    dst += imm
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) + uint32(insn.immediate)
            else:
                # 0x0f  add dst, src    dst += src
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) + uint32(self.vm.regs[insn.source])

            self.vm.regs[insn.destination] &= MAX_UINT32


    @disassemble("ALU", "sub")
    def _sub(self, op_opr, op_src, insn):
        if insn.op_class == OPC_ALU64:
            if op_src == 0:
                # 0x17  sub dst, imm    dst -= imm
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] - insn.immediate
            else:
                # 0x1f  sub dst, src    dst -= src
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] - self.vm.regs[insn.source]

            self.vm.regs[insn.destination] &= MAX_UINT64
        else:
            if op_src == 0:
                # 0x17  sub dst, imm    dst -= imm
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) - uint32(insn.immediate)
            else:
                # 0x1f  sub dst, src    dst -= src
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) - uint32(self.vm.regs[insn.source])

            self.vm.regs[insn.destination] &= MAX_UINT32


    @disassemble("ALU", "mul")
    def _mul(self, op_opr, op_src, insn):
        if insn.op_class == OPC_ALU64:
            if op_src == 0:
                # 0x27  mul dst, imm    dst *= imm
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] * insn.immediate
            else:
                # 0x2f  mul dst, src    dst *= src
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] * self.vm.regs[insn.source]

            self.vm.regs[insn.destination] &= MAX_UINT64
        else:
            if op_src == 0:
                # 0x27  mul dst, imm    dst *= imm
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) * uint32(insn.immediate)
            else:
                # 0x2f  mul dst, src    dst *= src
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) * uint32(self.vm.regs[insn.source])

            self.vm.regs[insn.destination] &= MAX_UINT32


    @disassemble("ALU", "div")
    def _div(self, op_opr, op_src, insn):
        try:
            if insn.op_class == OPC_ALU64:
                if op_src == 0:
                    # 0x37  div dst, imm    dst /= imm
                    self.vm.regs[insn.destination] = self.vm.regs[insn.destination] // insn.immediate
                else:
                    # 0x3f  div dst, src    dst /= src
                    self.vm.regs[insn.destination] = self.vm.regs[insn.destination] // self.vm.regs[insn.source]

                self.vm.regs[insn.destination] &= MAX_UINT64
            else:
                if op_src == 0:
                    # 0x37  div dst, imm    dst /= imm
                    self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) // uint32(insn.immediate)
                else:
                    # 0x3f  div dst, src    dst /= src
                    self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) // uint32(self.vm.regs[insn.source])

                self.vm.regs[insn.destination] &= MAX_UINT32
        except ZeroDivisionError as ex:
            self.vm.regs[insn.destination] = 0xffffffffffffffff
            raise

    @disassemble("ALU", "or")
    def _or(self, op_opr, op_src, insn):
        if op_src == 0:
            # 0x47  or dst, imm     dst |= imm
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] | insn.immediate
        else:
            # 0x4f  or dst, src     dst |= src
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] | self.vm.regs[insn.source]

        if insn.op_class != OPC_ALU64:
            self.vm.regs[insn.destination] &= MAX_UINT32
        else:
            self.vm.regs[insn.destination] &= MAX_UINT64


    @disassemble("ALU", "and")
    def _and(self, op_opr, op_src, insn):
        if op_src == 0:
            # 0x57  and dst, imm    dst &= imm
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] & insn.immediate
        else:
            # 0x5f  and dst, src    dst &= src
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] & self.vm.regs[insn.source]

        if insn.op_class != OPC_ALU64:
            self.vm.regs[insn.destination] &= MAX_UINT32
        else:
            self.vm.regs[insn.destination] &= MAX_UINT64


    @disassemble("ALU", "lsh")
    def _lsh(self, op_opr, op_src, insn):
        if op_src == 0:
            # 0x67  lsh dst, imm    dst <<= imm
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] << insn.immediate
        else:
            # 0x6f  lsh dst, src    dst <<= src
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] << self.vm.regs[insn.source]

        if insn.op_class != OPC_ALU64:
            self.vm.regs[insn.destination] &= MAX_UINT32
        else:
            self.vm.regs[insn.destination] &= MAX_UINT64


    @disassemble("ALU", "rsh")
    def _rsh(self, op_opr, op_src, insn):
        if insn.op_class == OPC_ALU64:
            if op_src == 0:
                # 0x77  rsh dst, imm    dst >>= imm (logical)
                #self.vm.regs[insn.destination] = (self.vm.regs[insn.destination] % (1 << 64)) >> insn.immediate
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] >> insn.immediate
            else:
                # 0x7f  rsh dst, src    dst >>= src (logical)
                #self.vm.regs[insn.destination] = (self.vm.regs[insn.destination] % (1 << 64)) >> self.vm.regs[insn.source]
                self.vm.regs[insn.destination] = self.vm.regs[insn.destination] >> self.vm.regs[insn.source]

            self.vm.regs[insn.destination] &= MAX_UINT64
        else:
            if op_src == 0:
                # 0x77  rsh dst, imm    dst >>= imm (logical)
                #self.vm.regs[insn.destination] = (uint32(self.vm.regs[insn.destination]) % (1 << 64)) >> insn.immediate
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) >> uint32(insn.immediate)
            else:
                # 0x7f  rsh dst, src    dst >>= src (logical)
                #self.vm.regs[insn.destination] = (uint32(self.vm.regs[insn.destination]) % (1 << 64)) >> self.vm.regs[insn.source]
                self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) >> uint32(self.vm.regs[insn.source])

            self.vm.regs[insn.destination] &= MAX_UINT32


    @disassemble("ALU", "neg")
    def _neg(self, op_opr, op_src, insn):
        if op_src == 0:
            # 0x87  neg dst         dst = -dst
            self.vm.regs[insn.destination] = -self.vm.regs[insn.destination]
        else:
            # 0x8f
            self._error(op_opr, op_src, insn)

        if insn.op_class != OPC_ALU64:
            self.vm.regs[insn.destination] &= MAX_UINT32
        else:
            self.vm.regs[insn.destination] &= MAX_UINT64


    @disassemble("ALU", "mod")
    def _mod(self, op_opr, op_src, insn):
        try:
            if insn.op_class == OPC_ALU64:
                if op_src == 0:
                    # 0x97  mod dst, imm    dst %= imm
                    self.vm.regs[insn.destination] = self.vm.regs[insn.destination] % insn.immediate
                else:
                    # 0x9f  mod dst, src    dst %= src
                    self.vm.regs[insn.destination] = self.vm.regs[insn.destination] % self.vm.regs[insn.source]

                self.vm.regs[insn.destination] &= MAX_UINT64
            else:
                if op_src == 0:
                    # 0x97  mod dst, imm    dst %= imm
                    self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) % uint32(insn.immediate)
                else:
                    # 0x9f  mod dst, src    dst %= src
                    self.vm.regs[insn.destination] = uint32(self.vm.regs[insn.destination]) % uint32(self.vm.regs[insn.source])

                self.vm.regs[insn.destination] &= MAX_UINT32
        except ZeroDivisionError as ex:
            self.vm.regs[insn.destination] = 0xffffffffffffffff
            raise


    @disassemble("ALU", "xor")
    def _xor(self, op_opr, op_src, insn):
        if op_src == 0:
            # 0xa7  xor dst, imm    dst ^= imm
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] ^ insn.immediate
        else:
            # 0xaf  xor dst, src    dst ^= src
            self.vm.regs[insn.destination] = self.vm.regs[insn.destination] ^ self.vm.regs[insn.source]

        if insn.op_class != OPC_ALU64:
            self.vm.regs[insn.destination] &= MAX_UINT32
        else:
            self.vm.regs[insn.destination] &= MAX_UINT64


    @disassemble("ALU", "mov")
    def _mov(self, op_opr, op_src, insn):
        if op_src == 0:
            # 0xb7 	mov dst, imm 	dst = imm
            self.vm.regs[insn.destination] = insn.immediate
        else:
            # 0xbf 	mov dst, src 	dst = src
            self.vm.regs[insn.destination] = self.vm.regs[insn.source]

        if insn.op_class != OPC_ALU64:
            self.vm.regs[insn.destination] &= MAX_UINT32
        else:
            self.vm.regs[insn.destination] &= MAX_UINT64


    @disassemble("ALU", "arsh")
    def _arsh(self, op_opr, op_src, insn):
        if insn.op_class == OPC_ALU64:
            if op_src == 0:
                # 0xc7  arsh dst, imm   dst >>= imm (arithmetic)
                self.vm.regs[insn.destination] = arit_rshift(
                    self.vm.regs[insn.destination],
                    insn.immediate,
                    sign_bit_pos=63)
            else:
                # 0xcf  arsh dst, src   dst >>= src (arithmetic)
                self.vm.regs[insn.destination] = arit_rshift(
                    self.vm.regs[insn.destination],
                    self.vm.regs[insn.source],
                    sign_bit_pos=63)

            self.vm.regs[insn.destination] &= MAX_UINT64
        else:
            if op_src == 0:
                # 0xc4  arsh32 dst, imm   dst >>= imm (arithmetic)
                self.vm.regs[insn.destination] = arit_rshift(
                    uint32(self.vm.regs[insn.destination]),
                    uint32(insn.immediate),
                    sign_bit_pos=31)
            else:
                # 0xcc  arsh32 dst, src   dst >>= src (arithmetic)
                self.vm.regs[insn.destination] = arit_rshift(
                    uint32(self.vm.regs[insn.destination]),
                    uint32(self.vm.regs[insn.source]),
                    sign_bit_pos=31)

            self.vm.regs[insn.destination] &= MAX_UINT32


    @disassemble("ALU", "endc")
    def _endc(self, op_opr, op_src, insn):
        if op_src == 1:
            # BigEndian
            # mem is little endian
            v = struct.unpack("<Q", struct.pack(">Q", self.vm.regs[insn.destination]))[0]
            if insn.immediate == 16:
                self.vm.regs[insn.destination] = (v & 0xffff000000000000) >> 48
            elif insn.immediate == 32:
                self.vm.regs[insn.destination] = (v & 0xffffffff00000000) >> 32
            elif insn.immediate == 64:
                self.vm.regs[insn.destination] = v
            else:
                self._error(op_opr, op_src, insn)
        else:
            # LittleEndian
            if insn.immediate == 16:
                self.vm.regs[insn.destination] = (self.vm.regs[insn.destination] & 0x000000000000ffff)
            elif insn.immediate == 32:
                self.vm.regs[insn.destination] = (self.vm.regs[insn.destination] & 0x00000000ffffffff)
            elif insn.immediate == 64:
                pass
            else:
                self._error(op_opr, op_src, insn)


    def _error(self, op_opr, op_src, insn, *args):
        raise Exception("Invalid ALU instruction: 0x{:016x}".format(insn.word))
