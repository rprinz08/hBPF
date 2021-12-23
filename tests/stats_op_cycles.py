#!/usr/bin/env python3

import sys
import re
from collections import namedtuple
# add search paths seen from project root folder
# (used for vscode test integration)
sys.path.insert(0, 'source')
sys.path.insert(0, 'tools/ubpf')
# add search paths when run from inside test folder
# (used when running test directly)
sys.path.insert(0, '../source')
sys.path.insert(0, '../tools/ubpf')

import unittest
import colour_runner.runner
import os
import gc
import tempfile
import struct
import re
import ntpath
import ubpf.assembler
import tools.testdata
from datetime import datetime
from migen import *
from litedram.frontend.bist import LFSR
from fpga.ram import *
from fpga.ram64 import *
from fpga.cpu import *

"""
This script determines the cycles for each opcode including opcode fetch.
It creates a CSV file for further processing. If OUPUT_MD_TABLE is set to
True, a markdown file will be created instead.
"""

OUPUT_MD_TABLE = False

stats = {}

def cpu_test(fd, opcode, cpu):
    ticks = 0
    done = False
    op = None
    ip = 0

    print(f"Testing ({opcode.name:15s}), ", end="")

    # Start CPU in reset an set input registers
    yield cpu.reset_n.eq(0)
    yield cpu.csr_r1.storage.eq(opcode.regs_in.r1)
    yield cpu.csr_r2.storage.eq(opcode.regs_in.r2)
    yield cpu.csr_r3.storage.eq(opcode.regs_in.r3)
    yield cpu.csr_r4.storage.eq(opcode.regs_in.r4)
    yield cpu.csr_r5.storage.eq(opcode.regs_in.r5)
    yield

    # Bring CPU out of reset
    yield cpu.reset_n.eq(1)
    yield

    # Process opcodes until CPU halts but no longer then 200 cycles.
    while ticks < 200 and not done:
        yield

        # Get current CPU state.
        halt = (yield cpu.halt)
        error = (yield cpu.error)
        state = (yield cpu.state)
        ip = (yield cpu.ip)
        if op is None:
            op = (yield cpu.opcode)
        r0 = (yield cpu.r0)
        r1 = (yield cpu.r1)
        r2 = (yield cpu.r2)
        r3 = (yield cpu.r3)
        r4 = (yield cpu.r4)
        r5 = (yield cpu.r5)

        if halt != 0:
            done = True

        ticks += 1

    # Subtract initial reset tick and final added exit op-code tick
    # (except for the 'exit' opcode itself)
    ticks -= (2 if opcode.name != "exit" else 1)

    # Write output
    if OUPUT_MD_TABLE:
        fd.write(f"|{opcode.name}|0x{op:02x}|{ticks}|\n")
    else:
        fd.write(f"\"{opcode.name}\",{ticks},{state},{halt},{error},"
            f"{r0},{r1},{r2},{r3},{r4},{r5}\n")

    failed = (opcode.regs_cmp.r1 != r1 or opcode.regs_cmp.r2 != r2 or
              opcode.regs_cmp.r3 != r3 or opcode.regs_cmp.r4 != r4 or
              opcode.regs_cmp.r5 != r5)

    if not failed and not opcode.ip is None:
        if opcode.ip != ip:
            failed = True

    print(f"opcode ({op:02x}) ... ", end="")
    if failed:
        print(f"\033[31mFAIL\033[0m, cycles ({ticks:4d})")
        if not opcode.ip is None:
            print(f"        IP {ip:016x} ({opcode.ip:016x})")
        print(f"        R1 {r1:016x} ({opcode.regs_cmp.r1:016x})")
        print(f"        R2 {r2:016x} ({opcode.regs_cmp.r2:016x})")
        print(f"        R3 {r3:016x} ({opcode.regs_cmp.r3:016x})")
        print(f"        R4 {r4:016x} ({opcode.regs_cmp.r4:016x})")
        print(f"        R5 {r5:016x} ({opcode.regs_cmp.r5:016x})")

        print(f"state: {state}, ip: {ip}, op: {op:02x}, "
            f"halt: {halt}, error: {error}")
    else:
        print(f"\033[32mOK  \033[0m, cycles ({ticks:4d})")

    b = stats.get(ticks, 0)
    stats[ticks] = b+1

    return


def opcode_cycles(fd, opcode):
    # Add additional 'exit' op-code to test ...
    code = ubpf.assembler.assemble(opcode.code + "\nexit")
    half_words = len(code) // 4
    pgm_mem = list(struct.unpack('>{}L'.format(half_words), code))

    # Create some dummy data memory ...
    data = b"\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"
    data_mem = list(data)

    cpu = CPU(pgm_init=pgm_mem, data_init=data_mem, simulation=True)
    run_simulation(cpu, cpu_test(fd, opcode, cpu), vcd_name="stats_op_cycles.vcd")


# Prepare named tuples to describe test
REGS = namedtuple('REGS', 'r1 r2 r3 r4 r5')
OPCODE = namedtuple('OPCODE', 'name code regs_in, regs_cmp,' +
    'ip, lddw')
OPCODE.__new__.__defaults__ = ("", "", REGS(0, 0, 0, 0, 0), REGS(0, 0, 0, 0, 0),
    None, False)

# Test definitions

#region ALU 64-Bit
opcodes_alu64 = [
    OPCODE("add imm",   "add r1, 1",
        REGS(1, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("add reg",   "add r1, r2",
        REGS(1, 1, 0, 0, 0),
        REGS(2, 1, 0, 0, 0)),
    OPCODE("sub imm",   "sub r1, 1",
        REGS(2, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("sub reg",   "sub r1, r2",
        REGS(2, 1, 0, 0, 0),
        REGS(1, 1, 0, 0, 0)),
    OPCODE("mul imm",   "mul r1, 2",
        REGS(2, 0, 0, 0, 0),
        REGS(4, 0, 0, 0, 0)),
    OPCODE("mul reg",   "mul r1, r2",
        REGS(2, 2, 0, 0, 0),
        REGS(4, 2, 0, 0, 0)),
    OPCODE("div imm",   "div r1, 2",
        REGS(5, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("div reg",   "div r1, r2",
        REGS(5, 2, 0, 0, 0),
        REGS(2, 2, 0, 0, 0)),
    OPCODE("or imm",    "or r1, 1",
        REGS(2, 0, 0, 0, 0),
        REGS(3, 0, 0, 0, 0)),
    OPCODE("or reg",    "or r1, r2",
        REGS(2, 1, 0, 0, 0),
        REGS(3, 1, 0, 0, 0)),
    OPCODE("and imm",   "and r1, 2",
        REGS(3, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("and reg",   "and r1, r2",
        REGS(3, 2, 0, 0, 0),
        REGS(2, 2, 0, 0, 0)),
    OPCODE("lsh imm",   "lsh r1, 4",
        REGS(1, 0, 0, 0, 0),
        REGS(16, 0, 0, 0, 0)),
    OPCODE("lsh reg",   "lsh r1, r2",
        REGS(1, 4, 0, 0, 0),
        REGS(16, 4, 0, 0, 0)),
    OPCODE("rsh imm",   "rsh r1, 3",
        REGS(16, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("rsh reg",   "rsh r1, r2",
        REGS(16, 3, 0, 0, 0),
        REGS(2, 3, 0, 0, 0)),
    OPCODE("neg",       "neg r1",
        REGS(3,                       0, 0, 0, 0),
        REGS(-3 & 0xffffffffffffffff, 0, 0, 0, 0)),
    OPCODE("mod imm",   "mod r1, 2",
        REGS(5, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("mod reg",   "mod r1, r2",
        REGS(5, 2, 0, 0, 0),
        REGS(1, 2, 0, 0, 0)),
    OPCODE("xor imm",   "xor r1, 2",
        REGS(7, 0, 0, 0, 0),
        REGS(5, 0, 0, 0, 0)),
    OPCODE("xor reg",   "xor r1, r2",
        REGS(7, 2, 0, 0, 0),
        REGS(5, 2, 0, 0, 0)),
    OPCODE("mov imm",   "mov r1, 2",
        REGS(4, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("arsh imm",   "arsh r1, 16",
        REGS(0x8000000000000000, 0, 0, 0, 0),
        REGS(0xffff800000000000, 0, 0, 0, 0)),
    OPCODE("arsh reg",   "arsh r1, r2",
        REGS(0x8000000000000000, 16, 0, 0, 0),
        REGS(0xffff800000000000, 16, 0, 0, 0)),
    OPCODE("le16",      "le16 r1",
        REGS(0xaabb, 0, 0, 0, 0),
        REGS(0xaabb, 0, 0, 0, 0)),
    OPCODE("le32",      "le32 r1",
        REGS(0xaabbccdd, 0, 0, 0, 0),
        REGS(0xaabbccdd, 0, 0, 0, 0)),
    OPCODE("le64",      "le64 r1",
        REGS(0xaabbccddeeff0011, 0, 0, 0, 0),
        REGS(0xaabbccddeeff0011, 0, 0, 0, 0)),
    OPCODE("be16",      "be16 r1",
        REGS(0xaabb, 0, 0, 0, 0),
        REGS(0xbbaa, 0, 0, 0, 0)),
    OPCODE("be32",      "be32 r1",
        REGS(0xaabbccdd, 0, 0, 0, 0),
        REGS(0xddccbbaa, 0, 0, 0, 0)),
    OPCODE("be64",      "be64 r1",
        REGS(0xaabbccddeeff0011, 0, 0, 0, 0),
        REGS(0x1100ffeeddccbbaa, 0, 0, 0, 0)),
]
#endregion

#region ALU 32-Bit
opcodes_alu32 = [
    OPCODE("add32 imm",   "add32 r1, 1",
        REGS(1, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("add32 reg",   "add32 r1, r2",
        REGS(1, 1, 0, 0, 0),
        REGS(2, 1, 0, 0, 0)),
    OPCODE("sub32 imm",   "sub32 r1, 1",
        REGS(2, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("sub32 reg",   "sub32 r1, r2",
        REGS(2, 1, 0, 0, 0),
        REGS(1, 1, 0, 0, 0)),
    OPCODE("mul32 imm",   "mul32 r1, 2",
        REGS(2, 0, 0, 0, 0),
        REGS(4, 0, 0, 0, 0)),
    OPCODE("mul32 reg",   "mul32 r1, r2",
        REGS(2, 2, 0, 0, 0),
        REGS(4, 2, 0, 0, 0)),
    OPCODE("div32 imm",   "div32 r1, 2",
        REGS(5, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("div32 reg",   "div32 r1, r2",
        REGS(5, 2, 0, 0, 0),
        REGS(2, 2, 0, 0, 0)),
    OPCODE("or32 imm",    "or32 r1, 1",
        REGS(2, 0, 0, 0, 0),
        REGS(3, 0, 0, 0, 0)),
    OPCODE("or32 reg",    "or32 r1, r2",
        REGS(2, 1, 0, 0, 0),
        REGS(3, 1, 0, 0, 0)),
    OPCODE("and32 imm",   "and32 r1, 2",
        REGS(3, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("and32 reg",   "and32 r1, r2",
        REGS(3, 2, 0, 0, 0),
        REGS(2, 2, 0, 0, 0)),
    OPCODE("lsh32 imm",   "lsh32 r1, 4",
        REGS(1, 0, 0, 0, 0),
        REGS(16, 0, 0, 0, 0)),
    OPCODE("lsh32 reg",   "lsh32 r1, r2",
        REGS(1, 4, 0, 0, 0),
        REGS(16, 4, 0, 0, 0)),
    OPCODE("rsh32 imm",   "rsh32 r1, 3",
        REGS(16, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("rsh32 reg",   "rsh32 r1, r2",
        REGS(16, 3, 0, 0, 0),
        REGS(2, 3, 0, 0, 0)),
    OPCODE("neg32",       "neg32 r1",
        REGS(3,                       0, 0, 0, 0),
        REGS(-3 & 0x00000000ffffffff, 0, 0, 0, 0)),
    OPCODE("mod32 imm",   "mod32 r1, 2",
        REGS(5, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("mod32 reg",   "mod32 r1, r2",
        REGS(5, 2, 0, 0, 0),
        REGS(1, 2, 0, 0, 0)),
    OPCODE("xor32 imm",   "xor32 r1, 2",
        REGS(7, 0, 0, 0, 0),
        REGS(5, 0, 0, 0, 0)),
    OPCODE("xor32 reg",   "xor32 r1, r2",
        REGS(7, 2, 0, 0, 0),
        REGS(5, 2, 0, 0, 0)),
    OPCODE("mov32 imm",   "mov32 r1, 2",
        REGS(4, 0, 0, 0, 0),
        REGS(2, 0, 0, 0, 0)),
    OPCODE("arsh32 imm",   "arsh32 r1, 16",
        REGS(0x0000000080000000, 0, 0, 0, 0),
        REGS(0x00000000ffff8000, 0, 0, 0, 0)),
    OPCODE("arsh32 reg",   "arsh32 r1, r2",
        REGS(0x0000000080000000, 16, 0, 0, 0),
        REGS(0x00000000ffff8000, 16, 0, 0, 0)),
]
#endregion

#region LD
opcodes_ld = [
    OPCODE("lddw",   "lddw r1, 0xbbaa998877665544",
        REGS(                 0, 0, 0, 0, 0),
        REGS(0xbbaa998877665544, 0, 0, 0, 0)),
]
#endregion

#region ST
opcodes_st = [
    OPCODE("stb",    "stb [r1+2], 0x40",
        REGS(1, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("sth",    "sth [r1+2], 0x5040",
        REGS(1, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("stw",    "stw [r1+2], 0x70605040",
        REGS(1, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
    OPCODE("stdw",   "stdw [r1+2], 0xb0a0908070605040",
        REGS(1, 0, 0, 0, 0),
        REGS(1, 0, 0, 0, 0)),
]
#endregion

#region LDX
opcodes_ldx = [
    OPCODE("ldxb",   "ldxb r2, [r1+2]",
        REGS(1,    0, 0, 0, 0),
        REGS(1, 0x44, 0, 0, 0)),
    OPCODE("ldxh",   "ldxh r2, [r1+2]",
        REGS(1,      0, 0, 0, 0),
        REGS(1, 0x5544, 0, 0, 0)),
    OPCODE("ldxw",   "ldxw r2, [r1+2]",
        REGS(1,          0, 0, 0, 0),
        REGS(1, 0x77665544, 0, 0, 0)),
    OPCODE("ldxdw",  "ldxdw r2, [r1+2]",
        REGS(1,                  0, 0, 0, 0),
        REGS(1, 0xbbaa998877665544, 0, 0, 0)),
]
#endregion

#region STX
opcodes_stx = [
    OPCODE("stxb",   "stxb [r1+2], r2",
        REGS(1, 0x40, 0, 0, 0),
        REGS(1, 0x40, 0, 0, 0)),
    OPCODE("stxh",   "stxh [r1+2], r2",
        REGS(1, 0x5040, 0, 0, 0),
        REGS(1, 0x5040, 0, 0, 0)),
    OPCODE("stxw",   "stxw [r1+2], r2",
        REGS(1, 0x70605040, 0, 0, 0),
        REGS(1, 0x70605040, 0, 0, 0)),
    OPCODE("stxdw",  "stxdw [r1+2], r2",
        REGS(1, 0xb0a0908070605040, 0, 0, 0),
        REGS(1, 0xb0a0908070605040, 0, 0, 0)),
]
#endregion

#region JMP
opcodes_jmp = [
    OPCODE("ja",        "ja +1234",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), 1234+1),
    OPCODE("jeq imm",   "jeq r1, 9, +4",
        REGS(9, 0, 0, 0, 0),
        REGS(9, 0, 0, 0, 0), 5),
    OPCODE("jeq reg",   "jeq r1, r2, +4",
        REGS(9, 9, 0, 0, 0),
        REGS(9, 9, 0, 0, 0), 5),
    OPCODE("jgt imm",   "jgt r1, 6, +2",
        REGS(7, 0, 0, 0, 0),
        REGS(7, 0, 0, 0, 0), 3),
    OPCODE("jgt reg",   "jgt r1, r2, +2",
        REGS(7, 6, 0, 0, 0),
        REGS(7, 6, 0, 0, 0), 3),
    OPCODE("jge imm",   "jge r1, 5, +4",
        REGS(5, 0, 0, 0, 0),
        REGS(5, 0, 0, 0, 0), 5),
    OPCODE("jge reg",   "jge r1, r2, +4",
        REGS(5, 4, 0, 0, 0),
        REGS(5, 4, 0, 0, 0), 5),
    OPCODE("jset imm",  "jset r1, 0x8, +4",
        REGS(9, 0, 0, 0, 0),
        REGS(9, 0, 0, 0, 0), None),
    OPCODE("jset reg",  "jset r1, r2, +4",
        REGS(9, 8, 0, 0, 0),
        REGS(9, 8, 0, 0, 0), None),
    OPCODE("jne imm",   "jne r1, 7, +543",
        REGS(6, 0, 0, 0, 0),
        REGS(6, 0, 0, 0, 0), 544),
    OPCODE("jne reg",   "jne r1, r2, +543",
        REGS(6, 7, 0, 0, 0),
        REGS(6, 7, 0, 0, 0), 544),
    OPCODE("jsgt imm",  "jsgt r1, 0xffffffff, +4",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jsgt reg",  "jsgt r1, r2, +4",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jsge imm",  "jsge r1, 0xffffffff, +5",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jsge reg",  "jsge r1, r2, +5",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    # OPCODE("call",       "call 0",
    #     REGS(0, 0, 0, 0, 0),
    #     REGS(0, 0, 0, 0, 0)),
    OPCODE("exit",      "exit",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jlt imm",   "jlt r1, 4, +2",
        REGS(3, 0, 0, 0, 0),
        REGS(3, 0, 0, 0, 0), 3),
    OPCODE("jlt reg",   "jlt r1, r2, +2",
        REGS(3, 4, 0, 0, 0),
        REGS(3, 4, 0, 0, 0), 3),
    OPCODE("jle imm",   "jle r1, 4, +99",
        REGS(4, 0, 0, 0, 0),
        REGS(4, 0, 0, 0, 0), 100),
    OPCODE("jle reg",   "jle r1, r2, +42",
        REGS(4, 5, 0, 0, 0),
        REGS(4, 5, 0, 0, 0), 43),
    OPCODE("jslt imm",  "jslt r1, 0xfffffffd, +2",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jslt reg",  "jslt r1, r1, +2",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jsle imm",  "jsle r1, 0xfffffffd, +1",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
    OPCODE("jsle reg",  "jsle r1, r2, +1",
        REGS(0, 0, 0, 0, 0),
        REGS(0, 0, 0, 0, 0), None),
]
#endregion

# Perform tests and produce output ...

# Open op-code statistics file.
date = datetime.now().strftime("%Y%m%d-%H%M%S")
output_file = f"./statistics/opcode_cycles_{date}.{'md' if OUPUT_MD_TABLE else 'csv'}"
with open(output_file, "w") as fd:

    if not OUPUT_MD_TABLE:
        fd.write("\"OpCode\",\"Cycles\",\"CPU State\",\"CPU Halt\",\"CPU Error\","
            "\"R1\",\"R1\",\"R2\",\"R3\",\"R4\",\"R5\"\n")

    print("\nALU 64-Bit")
    if OUPUT_MD_TABLE:
        fd.write("## ALU 64-Bit\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_alu64:
        opcode_cycles(fd, opcode)

    print("\nALU 32-Bit")
    if OUPUT_MD_TABLE:
        fd.write("\n## ALU 32-Bit\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_alu32:
        opcode_cycles(fd, opcode)

    print("\nLoad X")
    if OUPUT_MD_TABLE:
        fd.write("\n## Load X\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_ldx:
        opcode_cycles(fd, opcode)

    print("\nStore X")
    if OUPUT_MD_TABLE:
        fd.write("\n## Store X\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_stx:
        opcode_cycles(fd, opcode)

    print("\nLoad")
    if OUPUT_MD_TABLE:
        fd.write("\n## Load\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_ld:
        opcode_cycles(fd, opcode)

    print("\nStore")
    if OUPUT_MD_TABLE:
        fd.write("\n## Store\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_st:
        opcode_cycles(fd, opcode)

    print("\nJump")
    if OUPUT_MD_TABLE:
        fd.write("\n## Jump\n\n")
        fd.write("|Asm|OpCode|Cycles|\n")
        fd.write("|---|---|---|\n")
    for opcode in opcodes_jmp:
        opcode_cycles(fd, opcode)

    if OUPUT_MD_TABLE:
        fd.write("\n\n")

        t = {}
        s = sum(stats.values())
        for k, v in stats.items():
            pct = v * 100.0 / s
            t[k] = (v, pct)
        ts = sorted(t)
        fd.write("|Ticks|OpCodes|Pct%|\n")
        fd.write("|-----|-------|----|\n")
        for i in ts:
            fd.write(f"|{i}|{t[i][0]}|{t[i][1]}|\n")
