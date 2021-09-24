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
import time
from datetime import datetime
from migen import *
from litex.tools.remote.comm_uart import CommUART
from tools.hw_connect import HW_Connect
from fpga.ram import *
from fpga.ram64 import *
from fpga.cpu import *


class TestFPGA_HW(unittest.TestCase):


    # --------------------------------------------------------------------------
    # Configure hardware test for used target here:

    # Path to folder which contains CSR and config files. Can be absolute or
    # relative to this test file
    CFG_PATH = "../source/fpga/hw/arty-s7-50/debug"
    #CFG_PATH = "../source/fpga/hw/arty-s7-50-nic/debug"
    #CFG_PATH = "../source/fpga/hw/zybo-z7-20/debug"
    # --------------------------------------------------------------------------


    def setUp(self):
        # Determine path of configuration file and CSR definitions.
        if os.path.isabs(self.__class__.CFG_PATH):
            csr_csv = os.path.join(self.__class__.CFG_PATH, "csr.csv")
            config = os.path.join(self.__class__.CFG_PATH, ".config")
        else:
            csr_csv = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                self.__class__.CFG_PATH, "csr.csv")
            config = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                self.__class__.CFG_PATH, ".config")

        # Load configuration file.
        # Note: The configuration file is a Linux shell script which is also
        # included by other shell scripts. It may ony contain variable definitions
        # in the form 'export KEY=VALUE'. This shell script is read hear so that
        # its variables can be reused with this python test.
        config_arg = {}
        with open(config) as f:
            for line in f:
                if 'export' not in line:
                    continue
                if line.startswith('#'):
                    continue
                # Remove possible leading `export `
                # then, split name / value pair
                key, value = line.replace('export ', '', 1).strip().split('=', 1)
                config_arg[key] = value

        # Set some default values for attributes not defined in config file.
        uart_port = config_arg.get("TARGET_PORT", "/dev/ttyUSB1")
        uart_baudrate = config_arg.get("TARGET_SPEED", "115200")
        debug = int(config_arg.get("DEBUG", "0"), 0) > 0

        # Show current configuration.
        print("-"*50)
        print("Note: Be sure to configure '{}' ".format(__file__))
        print("to load the right configuration file for your target. Current ")
        print("set target configuration file is:")
        print("CONFIG: {}".format(config))
        if debug != 0:
            print("UART_PORT: {}".format(uart_port))
            print("UART_BAUDRATE: {}".format(uart_baudrate))
            print("DEBUG: {}".format(debug))
        print("-"*50)

        self.comm = HW_Connect(CommUART(uart_port, baudrate=uart_baudrate,
                                    csr_csv=csr_csv, debug=debug))
        self.comm.open()
        time.sleep(.4)


    def tearDown(self):
        self.comm.close()


    def check_datafile(self, filename, dump=False):
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

        # Prepare program memory.
        if 'raw' in td:
            code = b''.join(struct.pack('>Q', x) for x in td['raw'])
        else:
            code = ubpf.assembler.assemble(td['asm'])
        half_words = len(code) // 4
        pgm_mem = list(struct.unpack('>{}L'.format(half_words), code))
        td['raw'] = pgm_mem

        # Dump program memory for debug.
        # print("----- Program memory -----")
        # for i, opc in enumerate(pgm_mem):
        #     print("%04d: %08x" % (i, opc))

        # Dump out program memory binary
        if dump:
            with open(os.path.splitext(filename)[0] + ".pgm", "wb") as pgm_mem_file:
                pgm_mem_file.write(code)

        # Prepare data memory
        data_mem = td.get('mem')
        if isinstance(data_mem, bytes):
            data_mem = list(data_mem)
        td['mem'] = data_mem

        # Dump data memory for debug.
        # print("----- Date memory -----")
        # if data_mem is not None:
        #     for i, dat in enumerate(data_mem):
        #         print("%04d: %02x" % (i, dat))
        # else:
        #     print("No data memory")

        # Dump out program memory binary
        if dump and data_mem is not None:
            with open(os.path.splitext(filename)[0] + ".data", "wb") as data_mem_file:
                data_mem_file.write(bytes(data_mem))

        # Perform test
        self.cpu_test(td)

    def cpu_test(self, test_data, default_max_clock_cycles=1000, default_timout_ms=1000):
        """
        Perform actual test, control CPU signals like reset etc.
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
        disable_test = int(expected.get('disable_hw_test', str("0")))

        if disable_test == 1:
            self.skipTest("Testcase not available for HW test")

        # Control CPU via wishbone bridge.

        # Reset CPU.
        self.comm.cpu_reset()
        time.sleep(0.5)

        # Load program and data memory with test data.
        mem = test_data.get('mem')
        if mem is not None:
            self.comm.cpu_load_data(mem)
        self.comm.cpu_load_pgm(test_data['raw'])

        # set r1 - r5 input arguments
        args = test_data.get('args', {})
        r1 = int(str(args.get('r1', 0)), 0)
        r2 = int(str(args.get('r2', 0)), 0)
        r3 = int(str(args.get('r3', 0)), 0)
        r4 = int(str(args.get('r4', 0)), 0)
        r5 = int(str(args.get('r5', 0)), 0)
        self.comm.cpu_set_R1(r1)
        self.comm.cpu_set_R2(r2)
        self.comm.cpu_set_R3(r3)
        self.comm.cpu_set_R4(r4)
        self.comm.cpu_set_R5(r5)

        print("Input:")
        print("R1: ({:20}, 0x{:016x}), R2: ({:20}, 0x{:016x})".format(r1, r1, r2, r2))
        print("R3: ({:20}, 0x{:016x}), R4: ({:20}, 0x{:016x})".format(r3, r3, r4, r4))
        print("R5: ({:20}, 0x{:016x})".format(r5, r5))

        # Open test statistics file
        test_file = test_data.get("filename", None)
        stat_file = None
        if test_file is not None:
            stat_file = os.path.splitext(test_file)[0] + ".stats"
            sfd = open(stat_file, "a")

        # Start CPU.
        self.comm.cpu_run()

        # Wait til CPU enters halt state or timeout occurs.
        status = self.comm.cpu_get_status()
        halt = (status & 0x02) >> 1
        error = (status & 0x04) >> 2
        while not halt and clk_cnt <= max_clock_cycles:
            time.sleep(0.5)
            status = self.comm.cpu_get_status()
            halt = (status & 0x02) >> 1
            error = (status & 0x04) >> 2
            clk_cnt = self.comm.cpu_get_ticks()

        # Read back result in R0 and ticks needed to complete.
        r0 = self.comm.cpu_get_R0()
        clk_cnt = self.comm.cpu_get_ticks()

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
            sfd.write("\"{}\",{},{},{},{}\n".format(date, clk_cnt, halt, error, do_graph))
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
        self.check_datafile(filename, dump=True)
        gc.collect()
    return test

base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
for filename in tools.testdata.list_files(base_path):
    filebase = filename
    if filename.startswith(base_path):
        filebase = filename[len(base_path):]
    testname = 'test_' + '_'.join(os.path.splitext(filebase)[0].split(os.sep)).strip('_')
    setattr(TestFPGA_HW, testname, generate_testcase(filename))


if __name__ == '__main__':
    # Use colored testrunner instead of standard testrunner.
    #unittest.main()
    runner = colour_runner.runner.ColourTextTestRunner(sys.stdout, verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFPGA_HW)
    runner.run(suite)
