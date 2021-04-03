import sys
import os
import struct
from pprint import pprint
from colorama import Fore, Back, Style, init
from emulator.ebpf.constants import *
from emulator.ebpf.tools import *
from emulator.ebpf.vm_insn import Instruction
from emulator.ebpf.vm_opc import OPC


class VM():

    def __init__(self, mem=None, mem_size=MAX_PGM_MEM, stack_size=MAX_STACK,
                swap_endian=False, color=True, debug=False, call_handler=None):

        self.debug = debug

        # Init colored output.
        init(autoreset=True, strip=not color)

        # Prepare VM memory.
        if mem is None:
            mem = [0] * mem_size
        ml = len(mem)
        if ml > mem_size:
            raise Exception("Memory larger than maximum {}".format(mem_size))
        self.pgm_mem = mem
        if(ml < mem_size):
            self.pgm_mem.extend([0] * (mem_size - ml))

        # Context memory.
        self.data_mem = [0] * MAX_DATA_MEM

        # VM Stack.
        self.stack = [0] * stack_size

        # Prepare VM registers and create setters/getters for them.
        self.regs = [0] * MAX_REGS
        for r in range(MAX_REGS):
            setattr(self.__class__, "r{}".format(r), RegisterDescriptor(r))

        # Call handler, registry for helper functions
        self.call_handler = call_handler

        # Instruction pointer.
        self.ip = 0

        # Exit/return value.
        # If set by ebpf program, program stops and starts
        # again for new context or VM terminates when no more
        # contexts are available.
        self.exit_val = None

        # Runs VM in big- or little-endian mode depending pgm_mem byte-order.
        self.swap_endian = swap_endian

        # Current executed instruction
        self.cur_insn = None

        # Instantiate OpCode decoder.
        self.opc = OPC(self)


    # Reset VM.
    def reset(self):
        self.ip = 0


    # Start VM.
    def start(self):
        while self.exit_val is None:
            self.step()
        return self.exit_val


    # Returns current IP incremented by N. Does NOT change current IP.
    def inc_ip(self, n=1):
        return (self.ip + n) % len(self.pgm_mem)


    # Get current memory word where IP points to. VM internally always
    # assumes little-endian.
    def get_word(self):
        w = self.pgm_mem[self.ip]
        if self.swap_endian:
            w = struct.unpack("<Q", struct.pack(">Q", w))[0]
        return w


    # Process a single VM instruction.
    def step(self):
        self.ip = self.decode(self.get_word())
        return self.exit_val


    # Execute a VM instruction.
    def decode(self, word):
        self.cur_insn = Instruction(word)
        self.print_state()
        return self.opc.decode(self.cur_insn)


    # Print current VM rgisters.
    def print_regs(self):
        if not self.debug:
            return
        print("{}Regs {}".format(IND,
            ", ".join(
                "r{}:{}0x{:x}{}".format(i, Fore.CYAN, r, Fore.RESET)
                for i,r in enumerate(self.regs))))


    # Prints the VM state before executing the current instruction.
    def print_state(self):
        if not self.debug:
            return
        print("{}0x{:04x}: 0x{:016x}".format(
            Style.BRIGHT, self.ip, struct.unpack("<Q", struct.pack(">Q", self.cur_insn.word))[0]))
        self.cur_insn.print()
        self.print_regs()
