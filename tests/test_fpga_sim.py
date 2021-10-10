#!/usr/bin/env python3

import sys
import re
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


class CallHandler(Module):

    PRBS31 = [27, 30]
    PRBS23 = [17, 22]
    PRBS15 = [13, 14]
    PRBS7  = [ 5,  6]

    def __init__(self):
        self.func = func = Signal(64)
        self.r1 = r1 = Signal(64)
        self.r2 = r2 = Signal(64)
        self.r3 = r3 = Signal(64)
        self.r4 = r4 = Signal(64)
        self.r5 = r5 = Signal(64)
        self.ret = ret = Signal(64)
        self.stb = stb = Signal()
        self.ack = ack = Signal()
        self.err = err = Signal()

        # # #

        self.submodules.lfsr = lfsr = LFSR(31, n_state=31, taps=self.__class__.PRBS31)

        self.sync += [
            ack.eq(0),
            err.eq(0),
            If(stb,
                Case(func, {
                    0: [
                        ret.eq(
                            ((r1 & 0xff) << 32) |
                            ((r2 & 0xff) << 24) |
                            ((r3 & 0xff) << 16) |
                            ((r4 & 0xff) << 8) |
                            r5
                        )
                    ],
                    #6: [],
                    7: [
                        ret.eq(lfsr.o)
                    ],
                    0xff000001: [
                        # set LEDs to R1 bitmask
                    ],
                    "default": [
                        err.eq(1)
                    ]
                }),
                ack.eq(1)
            )
        ]


class TestFPGA_Sim(unittest.TestCase):

    def check_datafile(self, filename):
        """
        Given assembly source code and an expected result, run the eBPF program and
        verify that the result matches.
        """
        print()

        td = tools.testdata.read(filename)
        td['filename'] = filename
        td['name'] = os.path.splitext(os.path.split(filename)[1])[0]

        self.assertFalse('asm' not in td and 'raw' not in td,
                    'no asm or raw section in datafile')

        #self.assertFalse('result' not in td and 'error' not in td and 'error pattern' not in td,
        #            'no result or error section in datafile')

        # Prepare program memory
        if 'raw' in td:
            code = b''.join(struct.pack('>Q', x) for x in td['raw'])
        else:
            code = ubpf.assembler.assemble(td['asm'])
            td['raw'] = code
        half_words = len(code) // 4
        pgm_mem = list(struct.unpack('>{}L'.format(half_words), code))

        # Dump program memory for debug.
        #print("----- Program memory -----")
        #words = len(code) // 8
        #dbg_pgm_mem = list(struct.unpack('>{}Q'.format(words), code))
        #for i, opc in enumerate(dbg_pgm_mem):
        #    print("%04d: %016x" % (i, opc))

        # Prepare data memory
        data_mem = td.get('mem')
        if isinstance(data_mem, bytes):
            data_mem = list(data_mem)

        # Instantiate simulated CPU
        #vcd_file = os.path.abspath(os.path.dirname(__file__))
        #vcd_file = os.path.join(vcd_file, __name__ + ".vcd")
        vcd_file = os.path.abspath(os.path.dirname(filename))
        vcd_file = os.path.join(vcd_file, td['name'] + ".vcd")

        cpu = CPU(pgm_init=pgm_mem, data_init=data_mem, call_handler=CallHandler())
        run_simulation(cpu, self.cpu_test(cpu, td, default_max_clock_cycles=1000),
                       vcd_name=vcd_file)


    def cpu_test(self, cpu, test_data, default_max_clock_cycles=1000):
        """
        Perform actual test, control CPU signals like clock etc.
        """

        clk_cnt = 0

        # Prepare result to check
        result = None
        if 'result' in test_data:
            result = int(test_data['result'], 0)

        expected_error = 0
        expected_error_msg = None
        if 'error' in test_data:
            expected_error = 1
            expected_error_msg = test_data['error']

        expected = dict(re.findall(r'(\S+)\s*=\s*(".*?"|\S+)', test_data.get('expected', '')))
        #print(expected)
        expected_halt = 1 if int(expected.get('halt', '1'), 0) > 0 else 0
        # this can override error section above
        expected_error = 1 if int(expected.get('error', str(expected_error)), 0) > 0 else 0
        max_clock_cycles = int(expected.get('clocks', str(default_max_clock_cycles)), 0)
        disable_test = int(expected.get('disable_sim_test', str("0")))

        if disable_test == 1:
            self.skipTest("Testcase not available for Simulator test")

        # Start with 5 clocks in reset.
        yield cpu.reset_n.eq(0)
        for i in range(5):
            yield

        # set r1 - r5 input arguments
        args = test_data.get('args', {})
        r1 = int(str(args.get('r1', 0)), 0)
        r2 = int(str(args.get('r2', 0)), 0)
        r3 = int(str(args.get('r3', 0)), 0)
        r4 = int(str(args.get('r4', 0)), 0)
        r5 = int(str(args.get('r5', 0)), 0)
        yield cpu.csr_r1.storage.eq(r1)
        yield cpu.csr_r2.storage.eq(r2)
        yield cpu.csr_r3.storage.eq(r3)
        yield cpu.csr_r4.storage.eq(r4)
        yield cpu.csr_r5.storage.eq(r5)
        yield

        print("Input:")
        print("R1: ({:20}, 0x{:016x}), R2: ({:20}, 0x{:016x})".format(r1, r1, r2, r2))
        print("R3: ({:20}, 0x{:016x}), R4: ({:20}, 0x{:016x})".format(r3, r3, r4, r4))
        print("R5: ({:20}, 0x{:016x})".format(r5, r5))

        # Open op-code statistics file
        test_file = test_data.get("filename", None)
        stat_file = None
        if test_file is not None:
            stat_file = os.path.splitext(test_file)[0] + ".stats"
            sfd = open(stat_file, "a")

        # End reset.
        yield cpu.reset_n.eq(1)
        yield

        # Clock CPU until halt, error or max clock cycles reached.
        halt = (yield cpu.halt)
        error = (yield cpu.error)
        r0 = (yield cpu.r0)

        while halt == 0 and clk_cnt <= max_clock_cycles:
            halt = (yield cpu.halt)
            error = (yield cpu.error)
            r0 = (yield cpu.r0)
            yield
            if not halt:
                clk_cnt += 1

        print("Output:")
        print("Clock cycles: ({}), halt: ({}), error: ({}), R0: ({:20}, 0x{:016x})".format(
            clk_cnt,
            "LOW" if halt == 0 else "HIGH",
            "LOW" if error == 0 else "HIGH", r0, r0))

        # Write clock cycles for this test to statistics file
        if stat_file is not None:
            do_graph = int(str(args.get('graph', 1)), 0)
            do_graph = 1 if do_graph > 0 else 0
            date = datetime.now().strftime("%Y%m%d-%H%M%S")
            sfd.write("\"SIM\",\"{}\",{},{},{},{}\n".format(date, clk_cnt, halt, error, do_graph))
            sfd.close()

        # Check result
        #if not expected_error:
        #    self.assertEqual(error, 0,
        #        "Action completes with error signal HIGH")
        #else:
        #    self.assertEqual(error, 1,
        #        "Action expected to complete with error signal HIGH but was LOW")
        #    if error_expected_msg is not None:
        #        print("Expected error: {}".format(error_expected_msg))
        #    return

        self.assertEqual(error, expected_error,
            ("Action does not complete with expected error signal level; " +
                "was {} should be {}").format(error, expected_error))

        self.assertLessEqual(clk_cnt, max_clock_cycles,
            "Action did not complete within max clock cycles ({})".format(
                max_clock_cycles))

        self.assertEqual(halt, expected_halt,
            ("Action does not complete with expected halt signal level; " +
                "was {} should be {}").format(halt, expected_halt))

        if result is not None:
            self.assertEqual(r0, result,
                ("Received result ({}, 0x{:08x}) not equal expected " +
                "({}, 0x{:08x})").format(
                    r0, r0, result, result))


# Generate a testcase for each test data file when module is loaded.
def generate_testcase(filename):
    def test(self):
        gc.collect()
        self.check_datafile(filename)
        gc.collect()
    return test

base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
for filename in tools.testdata.list_files(base_path):
    filebase = filename
    if filename.startswith(base_path):
        filebase = filename[len(base_path):]
    testname = 'test_' + '_'.join(os.path.splitext(filebase)[0].split(os.sep)).strip('_')
    setattr(TestFPGA_Sim, testname, generate_testcase(filename))


if __name__ == '__main__':
    # Use colored testrunner instead of standard testrunner.
    #unittest.main()
    runner = colour_runner.runner.ColourTextTestRunner(sys.stdout, verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFPGA_Sim)
    runner.run(suite)
