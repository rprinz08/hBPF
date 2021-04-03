import sys
import os
import struct
from pprint import pprint
from emulator.ebpf.constants import *
from emulator.ebpf.tools import *
from emulator.ebpf.vm_alu import ALU
from emulator.ebpf.vm_jump import JMP
from emulator.ebpf.vm_load import LOAD
from emulator.ebpf.vm_store import STORE


class OPC():

    def __init__(self, vm):
        self.vm = vm
        # Instantiate sub-decoders.
        self.alu = ALU(vm)
        self.jmp = JMP(vm)
        self.load = LOAD(vm)
        self.store = STORE(vm)

        # OpCode decoder.
        self._decoder = {
            OPC_LD    : self.load.decode,
            OPC_LDX   : self.load.decode,
            OPC_ST    : self.store.decode,
            OPC_STX   : self.store.decode,
            OPC_ALU   : self.alu.decode,
            OPC_JMP   : self.jmp.decode,
            OPC_RES   : self._error,
            OPC_ALU64 : self.alu.decode
        }


    def decode(self, insn):
        return self._decoder.get(insn.op_class, self._error)(insn)


    def _error(self, insn, *args):
        raise Exception("Invalid instruction class: 0x{:016x}".format(insn.word))
