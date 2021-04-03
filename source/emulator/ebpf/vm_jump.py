import sys
import os
import struct
from pprint import pprint

from emulator.ebpf.constants import *
from emulator.ebpf.tools import *


class JMP():

    def __init__(self, vm):
        self.vm = vm

        # Decoder for jump OpCodes.
        self._decoder = {
            JMP_JA   : self._ja,
            JMP_JEQ  : self._jeq,
            JMP_JGT  : self._jgt,
            JMP_JGE  : self._jge,
            JMP_JSET : self._jset,
            JMP_JNE  : self._jne,
            JMP_JSGT : self._jsgt,
            JMP_JSGE : self._jsge,
            JMP_CALL : self._call,
            JMP_EXIT : self._exit,
            JMP_JLT  : self._jlt,
            JMP_JLE  : self._jle,
            JMP_JSLT : self._jslt,
            JMP_JSLE : self._jsle
        }


    def decode(self, insn):
        op_src = (insn.op_code >> 3) & 0b1
        op_opr = (insn.op_code >> 4) & 0b1111

        return self._decoder.get(op_opr, self._error)(op_opr, op_src, insn) + 1


    # Jump handlers.
    @disassemble("JMP", "ja")
    def _ja(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x05  ja +off         PC += off
            return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x0d
            self._error(op_opr, op_src, insn)


    @disassemble("JMP", "jeq")
    def _jeq(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x15  jeq dst, imm, +off   PC += off if dst == imm
            if self.vm.regs[insn.destination] == insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x1d  jeq dst, src, +off   PC += off if dst == src
            if self.vm.regs[insn.destination] == self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jgt")
    def _jgt(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x25  jgt dst, imm, +off   PC += off if dst > imm
            if self.vm.regs[insn.destination] > insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x2d  jgt dst, src, +off   PC += off if dst > src
            if self.vm.regs[insn.destination] > self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jge")
    def _jge(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x35  jge dst, imm, +off   PC += off if dst >= imm
            if self.vm.regs[insn.destination] >= insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x3d  jge dst, src, +off   PC += off if dst >= src
            if self.vm.regs[insn.destination] >= self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jset")
    def _jset(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x45  jset dst, imm, +off  PC += off if dst & imm
            if (self.vm.regs[insn.destination] & insn.immediate) == insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x4d  jset dst, src, +off  PC += off if dst & src
            if (self.vm.regs[insn.destination] & self.vm.regs[insn.source]) == self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jne")
    def _jne(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x55  jne dst, imm, +off   PC += off if dst != imm
            if self.vm.regs[insn.destination] != insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x5d  jne dst, src, +off   PC += off if dst != src
            if self.vm.regs[insn.destination] != self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jsgt")
    def _jsgt(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x65  jsgt dst, imm, +off  PC += off if dst > imm (signed)
            if int32(self.vm.regs[insn.destination]) > insn.immediate_s:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x6d  jsgt dst, src, +off  PC += off if dst > src (signed)
            if int32(self.vm.regs[insn.destination]) > int32(self.vm.regs[insn.source]):
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jsge")
    def _jsge(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x75  jsge dst, imm, +off  PC += off if dst >= imm (signed)
            if int32(self.vm.regs[insn.destination]) >= insn.immediate_s:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0x7d  jsge dst, src, +off  PC += off if dst >= src (signed)
            if int32(self.vm.regs[insn.destination]) >= int32(self.vm.regs[insn.source]):
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "call")
    def _call(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x85  call imm             Function call
            # TODO: return stack
            if isinstance(self.vm.call_handler, dict):
                helper = self.vm.call_handler.get(insn.immediate, None)
                if helper is None:
                    self._error(op_opr, op_src, insn)
                else:
                    self.vm.r0 = helper(self.vm.r1, self.vm.r2, self.vm.r3,
                                        self.vm.r4, self.vm.r5)
                return self.vm.ip
            else:
                self._error(op_opr, op_src, insn)
        else:
            # 0x8d
            self._error(op_opr, op_src, insn)


    #@disassemble("JMP", "exit")
    def _exit(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0x95  exit            return r0
            # TODO: return from call ???
            self.vm.exit_val = self.vm.r0
            return self.vm.ip
        else:
            # 0x9d
            self._error(op_opr, op_src, insn)


    @disassemble("JMP", "jlt")
    def _jlt(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0xa5  jlt dst, imm, +off   PC += off if dst < imm
            if self.vm.regs[insn.destination] < insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0xad  jlt dst, src, +off   PC += off if dst < src
            if self.vm.regs[insn.destination] < self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jle")
    def _jle(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0xb5  jle dst, imm, +off   PC += off if dst <= imm
            if self.vm.regs[insn.destination] <= insn.immediate:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0xbd  jle dst, src, +off   PC += off if dst <= src
            if self.vm.regs[insn.destination] <= self.vm.regs[insn.source]:
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jslt")
    def _jslt(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0xc5  jslt dst, imm, +off  PC += off if dst < imm (signed)
            if int32(self.vm.regs[insn.destination]) < insn.immediate_s:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0xcd  jslt dst, src, +off  PC += off if dst < src (signed)
            if int32(self.vm.regs[insn.destination]) < int32(self.vm.regs[insn.source]):
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    @disassemble("JMP", "jsle")
    def _jsle(self, op_opr, op_src, insn):
        if op_src == JMP_K:
            # 0xd5  jsle dst, imm, +off  PC += off if dst <= imm (signed)
            if int32(self.vm.regs[insn.destination]) <= insn.immediate_s:
                return self.vm.inc_ip(n=insn.offset_s)
        else:
            # 0xdd  jsle dst, src, +off  PC += off if dst <= src (signed)
            if int32(self.vm.regs[insn.destination]) <= int32(self.vm.regs[insn.source]):
                return self.vm.inc_ip(n=insn.offset_s)
        return self.vm.ip


    def _error(self, op_opr, op_src, insn, *args):
        raise Exception("Invalid JUMP instruction: 0x{:016x}".format(insn.word))
